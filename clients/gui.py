import socket  # Importamos librería para comunicación en red a través de TCP/IP
import threading  # Importamos hilos para procesos asíncronos en 2do plano sin congelar la ventana gráfica
import tkinter as tk  # Importamos librería gráfica estándar de Python (Tkinter) bajo el alias corto "tk"
from tkinter import simpledialog, messagebox, scrolledtext  # Importamos componentes de uso específico de Tkinter (Diálogos de input rápidos, alertas emergentes y áreas de texto con scroll)
import sys  # Importamos syscalls de Sistema Operativo para forzar cierres (ej. sys.exit)

HOST = "127.0.0.1"  # Dirección IP a la que la App intentará llamar. "127.0.0.1" es localhost (este mismo compu)
PORT = 5050  # El Puerto TCP que debe coincidir con el puerto escuchando en el `server.py`


class ChatClientGUI:
    """Clase principal orientada a objetos que encapsula todoterreno la ventana gráfica del Cliente de chat."""
    def __init__(self, master):
        self.master = master  # Almacena el objeto de la ventana raíz (Root Window) inyectada en Main()
        self.master.title("Computo Chat")  # Damos nombre/título al borde superior de la App en el OS
        self.master.geometry("500x600")  # Modificamos resolución default prevía, ancho x alto píxeles
        self.master.configure(bg="#2E3440")  # Seteamos color default de fondo general
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Instanciamos aquí el Socket túnel cliente que logrará el milagro del chat
        self.file = None  # Lo usaremos luego de enganchar conexión para leer los streams como archivos texto
        self.running = False  # Bandera stateful Booleana (Interruptor prendido/apagado) para definir estado vital global de los sub-procesos o hilos.

        self.setup_ui()  # Ejecutamos nuestra gran función armador de bloques e interfaz que definimos abajo
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)  # Al hacer click a la 'X' roja de la ventana de SO, atrapar ese evento y redirigirlo a nuestro destrozador controlado llamado on_closing.
        
        # Una vez los botones ya pintaron y la UI está "dibujada", enclavamos el conectador TCP en 100ms
        self.master.after(100, self.connect_to_server)

    def setup_ui(self):
        """Super función que sirve de lienzo para 'pintar/colocar' todos los widgets/elementos (Botones, listas, cuadros)."""
        # -- SECCIÓN PALETA DE COLORES (CATPPUCCIN) -- 
        self.bg_color = "#1E1E2E"       # Color Fondo general oscuro principal
        self.sidebar_color = "#181825"  # Color Panel Lateral izquierdo oscurecido 
        self.panel_color = "#313244"    # Color Plástico oscuro para zonas botones o inputs
        self.text_color = "#CDD6F4"     # Tinta blanquizca para texto legible 
        self.accent_color = "#89B4FA"   # Tinta Azul chillón principal decorativo
        self.accent_hover = "#B4BEFE"   # Azul blanqueado para efecto ratón 'Flotando Arriba'
        self.self_bubble = "#A6E3A1"    # Letra de Burbuja verde para identificar quién escribe "User actual"
        self.other_bubble = "#89DCEB"   # Letra celeste para identificar chateo general del resto extraños
        self.system_text = "#F38BA8"    # Letras rojizas para logs alertas de red server.

        self.master.geometry("800x600") # Hacer la ventana mucho más ancha para caber el sidebar
        self.master.configure(bg=self.bg_color) # Aplicar a fondo main general esa paleta
        
        # Fuentes de sistema guardadas como variables para reciclar rápido
        self.font_main = ("Helvetica", 14)  # Fuente normal 14
        self.font_bold = ("Helvetica", 14, "bold")  # Negrilla
        self.font_small = ("Helvetica", 10, "italic")  # Cursiva chiquita
        
        # --- LÓGICA DE GESTOR PESTAÑAS Y CANALES ---
        self.current_channel = "Global"  # String flag diciendo de estado base que siempre arrancamos viendo el canal Global
        self.tabs = {}  # Diccionario vital que albergará información interna sobre qué pestaña y widget es cual: {"NombreCanal": {"frame": frameObj, "text_area": textareaObj}}

        # --- ESTILOS DE COMPONENTES INTERNOS ---
        from tkinter import ttk  # TTK es como un reskin (mejorador de texturas modernas) de Tkinter base
        style = ttk.Style()  # Invocamos al sastre de texturas
        style.theme_use('default')  # Aplicar la base virgen 
        style.configure("TNotebook", background=self.bg_color, borderwidth=0)  # Pestañas invisibles bordes
        style.configure("TNotebook.Tab", background=self.sidebar_color, foreground=self.text_color, padding=[10, 5], font=self.font_bold)  # Diseño a botón de pestaña
        style.map("TNotebook.Tab", background=[("selected", self.panel_color)], foreground=[("selected", self.accent_color)])  # Color Azul extra para la solapa activa actual donde estás parado

        # Contenedor Principal Divisible tipo 'Split-Screen' ajustable de lado a lado (PanedWindow)
        self.paned_window = tk.PanedWindow(self.master, orient=tk.HORIZONTAL, bg=self.bg_color, sashwidth=5, bd=0)
        self.paned_window.pack(fill=tk.BOTH, expand=True)  # Empaquetamos expandiendo el split a que ocupe de punta a punta toda zona libre de la app madre

        # ====== PANEL IZQUIERDO SIDEBAR ======
        self.sidebar_frame = tk.Frame(self.paned_window, bg=self.sidebar_color, width=200)  # Cúbico izquierdo
        self.paned_window.add(self.sidebar_frame, minsize=150)  # Metido al lado izquierdo del split-screen
        
        # Botoncito superior estático que siempe te devolverá a la plaza general Global
        tk.Button(self.sidebar_frame, text="🌍 Global Chat", bg=self.panel_color, fg=self.text_color, borderwidth=0, command=lambda: self.switch_channel("Global")).pack(fill=tk.X, pady=5, padx=5)

        # Label Título Usuarios Conectados
        tk.Label(self.sidebar_frame, text="👥 Usuarios", bg=self.sidebar_color, fg=self.text_color, font=self.font_small).pack(fill=tk.X, pady=(10,0))
        # Caja lista interactiva de los usuarios que nos mandó la data server (Listbox). Clickear un ítem manda DM
        self.users_listbox = tk.Listbox(self.sidebar_frame, bg=self.sidebar_color, fg=self.text_color, selectbackground=self.panel_color, borderwidth=0, highlightthickness=0)
        self.users_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.users_listbox.bind("<<ListboxSelect>>", self.on_user_select)  # Amarra el evento 'Click-Mouse en un ítem' hacia la función lógica on_user_select

        # Label Título Grupos
        tk.Label(self.sidebar_frame, text="💬 Grupos", bg=self.sidebar_color, fg=self.text_color, font=self.font_small).pack(fill=tk.X, pady=(10,0))
        # Caja lista interactiva para grupos donde si les hago click manda comando /join al servidor y abre pestaña
        self.groups_listbox = tk.Listbox(self.sidebar_frame, bg=self.sidebar_color, fg=self.text_color, selectbackground=self.panel_color, borderwidth=0, highlightthickness=0)
        self.groups_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.groups_listbox.bind("<<ListboxSelect>>", self.on_group_select)  # Click-mouse -> ejecuta on_group_select
        
        # Botón inferior que abre pop-up para crear un room tú mismo
        tk.Button(self.sidebar_frame, text="➕ Crear/unirse a Grupo", bg=self.panel_color, fg=self.text_color, borderwidth=0, command=self.prompt_group).pack(fill=tk.X, pady=5, padx=5)

        # ====== PANEL DERECHO: MAIN CHAT AREA ======
        self.chat_frame = tk.Frame(self.paned_window, bg=self.bg_color)  # Marco principal masivo
        self.paned_window.add(self.chat_frame, minsize=400)  # Agregado directo al carril derecho del split-screen

        # Inyectamos el 'Cuaderno Pestañas' múltiple arriba (Notebook de TTK)
        self.notebook = ttk.Notebook(self.chat_frame)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)  # Atrapar el evento cuando un humano pasa del Chat A al Chat B y activar validación

        # Creamos automáticamente la pestaña Global por defecto obligatoria de arraque inicial
        self.create_tab("Global")
        
        # Barra Inferior para insertar Mensajes y apretar Enviar
        self.bottom_frame = tk.Frame(self.chat_frame, bg=self.panel_color, pady=10, padx=10)
        self.bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)  # Packeado y pegado (side=tk.BOTTOM) al suelo absoluto de la ventana
        
        self.entry_container = tk.Frame(self.bottom_frame, bg=self.panel_color)
        self.entry_container.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(10, 10))  # Contenedor del text-box a su izquierda

        # Caje de Texto de Input Teclado donde redactaremos las maravillas (Entry)
        self.msg_entry = tk.Entry(
            self.entry_container,
            font=self.font_main, bg="#45475A", fg=self.text_color,  # Tintas
            insertbackground=self.text_color, borderwidth=0, highlightthickness=1,  # Color de rayita vertical inserción "insertbg"
            highlightcolor=self.accent_color, highlightbackground="#45475A"  # Borde azul hover en text box
        )
        self.msg_entry.pack(expand=True, fill=tk.X, ipady=12, padx=5, pady=5)
        self.msg_entry.bind("<Return>", self.send_message)  # Conectar que la tecla "Enter=Return" invoque envio de mensaje
        
        # Botón de envio visual (Para el que no gusta usar Enter en Desktop)
        self.send_btn = tk.Button(
            self.bottom_frame, text="Enviar ➔",
            font=self.font_bold, bg=self.accent_color, fg="#11111B",
            activebackground=self.accent_hover, borderwidth=0,
            cursor="hand2", command=self.send_message  # Invoca la función disparadora de MSGs
        )
        self.send_btn.pack(side=tk.RIGHT, ipadx=15, ipady=8, padx=(0, 10))  # A la derecha!
        
        # Congelamos temporalmente inputs de uso. Hasta que el LOGIN apruebe
        self.msg_entry.config(state='disabled')
        self.send_btn.config(state='disabled')

    def create_tab(self, channel_name):
        """Función fundamental instanciadora de solapas (Pestañuelas/Canales de charleta extra)."""
        if channel_name not in self.tabs:  # Solo actua si no existia una antes registrada en la dict interna tabs.
            frame = tk.Frame(self.notebook, bg=self.bg_color)  # Crea la mesa base
            
            # ScrolledText genera el cuadro masivo y le pone la barrita scroll lateral
            chat_area = scrolledtext.ScrolledText(
                frame, wrap=tk.WORD, state='disabled',  # Disabled porque texto solo lo escribe la IP local, el HUMANO no debe romper letras como bloc de Notas del centro visual
                bg=self.bg_color, fg=self.text_color,
                font=self.font_main, borderwidth=0, highlightthickness=0,
                padx=20, pady=20
            )
            chat_area.pack(expand=True, fill=tk.BOTH)  # Llena toda la ventana de esa pestaña en base al padre frame.
            
            # Configura 'Tags o Etiquetas HTML-like' in-built de Tkinter. Al texto marcado "right" se pintará a la derecha 
            chat_area.tag_config("right", justify="right", foreground=self.self_bubble)  # Tag Yo
            chat_area.tag_config("left", justify="left", foreground=self.other_bubble)  # Tag Extranjeros
            chat_area.tag_config("center", justify="center", foreground=self.system_text, font=self.font_small)  # Tag para Anuncios de Sistema
            
            self.notebook.add(frame, text=f" {channel_name} ")  # Finaliza ensamblando este cuadro al control Notebook agregandole el Nombre superior
            self.tabs[channel_name] = {"frame": frame, "text_area": chat_area}  # Guardamos la llave objeto en nuestra db local.

    def switch_channel(self, channel_name):
        """Cambia a una solapa específica, creándola mágicamente de golpe si no existiera antes."""
        self.current_channel = channel_name  # Cambia la variable de enfoque para que la función "Send MSG" sepa pa donde arrojar
        self.create_tab(channel_name)  # Validación veloz por si es click a un usuario nuevo.
        
        # Seleccionar la pestaña activa frontal robando foco del Notebook
        tab_id = self.tabs[channel_name]["frame"]  # Obtiene el Frame literal en memoria
        self.notebook.select(tab_id)  # API call a TK para pasarla al frente
        
        # Limpiar lo azul (Selección Activa Visual) que pudiera estar trancado en los listados del Sidebar de afuera.
        self.users_listbox.selection_clear(0, tk.END)
        self.groups_listbox.selection_clear(0, tk.END)

    def on_tab_changed(self, event):
        """Disparador interno (Trigger). Actualiza el current_channel vital cuando el Humano con ratón explora manualmente otras solapas."""
        selected_tab = event.widget.select()  # Recolecta del widget evento, String de la Pestaña en foco
        if selected_tab:  # Si agarró info válida..
            for channel_name, data in self.tabs.items():  # Barremos todo nuestro inventario..
                if str(data["frame"]) == selected_tab:  # Hasta igualar el ID que Tkinter reportó con el nuestró.
                    self.current_channel = channel_name  # Efectuamos el cambio de "Canal de escritura".
                    # Remover el Emoji '🔴' rojizo notificador de Nuevos Mensajes de ese canal si es que tuviese.
                    self.notebook.tab(selected_tab, text=f" {channel_name} ") 
                    break

    def on_user_select(self, event):
        """Detecta Clicado a la lista caja interactiva de Usuarios para generar PMs."""
        selection = event.widget.curselection()  # Saca la Info del clic. (Arroja un tuple)
        if selection:
            user = event.widget.get(selection[0])  # Convertir índice del clíc al Texto real ("Pablito")
            self.switch_channel(f"@{user}")  # Invocar macro de Cambiar canal, agregando el prefijo arroba para denotar que será Private

    def on_group_select(self, event):
        """Detecta Clicado a la lista caja de Grupos visual para hacer un Join automático rápido."""
        selection = event.widget.curselection()
        if selection:
            group = event.widget.get(selection[0])  # Absorbe el nombre real text string ('gatosRoom')
            self.sock.sendall((f"/join {group}\n").encode())  # De forma oculta manda comando nativo legacy "/join name" de lado Cliente-Servidor directo
            self.switch_channel(f"#{group}")  # Muda tu mirada inmediatamente a la pestaña de ese chat. (Arrancando con hashtag denotativo grupo)

    def prompt_group(self):
        """Lanza el Modal Cuadrado visual asíncrono para pedirte con Letras el grupo creadizo o acoplable."""
        g_name = simpledialog.askstring("Grupo", "Nombre del grupo nuevo o a unirse (sin espacios):", parent=self.master)
        if g_name:  # Si diose a Aceptar y escribió texto..
            # Al darle, escupe los comandos para ambos, si ya existe el join hace eco, si no el creategroup hace magia.
            self.sock.sendall((f"/creategroup {g_name}\n").encode())
            self.sock.sendall((f"/join {g_name}\n").encode())
            self.switch_channel(f"#{g_name}")  # Refleja con pestaña instantánea

    def connect_to_server(self):
        """Sub-Rutina Inicial. Intenta ejecutar la pedida de enchufe al servidor TCP general."""
        try:
            self.sock.connect((HOST, PORT))  # Empezará petición Three-Way Handshake TCP de conexión real
            self.file = self.sock.makefile("r")  # Empaqueta y envuelve el cable (Socket) como un FileReader normal de lectura rápida de strings.
        except Exception as e:
            # Ups! Excepción mortal, Servidor offline o apagado, firewall o IP mal escrita.. mostramos PopUp Crash.
            messagebox.showerror("Error de conexión", f"No se pudo conectar al servidor:\n{e}")
            self.on_closing()  # Invocamos al verdugo para limpiar la App (Auto-Destrucción sana)
            return

        self.authenticate()  # El HandShake dio éxito. Aún no tienes identidad. Corre función de registro.

    def authenticate(self):
        """Bucle inicial forzado por GUI Modal de Registro Nombre, no te dejará avanzar a la App Main sin responder al Servidor tu identidad real."""
        try:
            prompt = self.file.readline().strip()  # Recoge el saludo universal del servidor pidiendo Identificación ("Enter username:")
        except:
            # Fallo por servidor botándonos antes de hablar
            messagebox.showerror("Error", "Desconectado del servidor de arranque")
            self.on_closing()
            return

        while True:
            # Ejecutamos panel flotador de sistema pidiendo que el humano ingrese datos
            username = simpledialog.askstring("Identificación", prompt, parent=self.master)
            if not username:  # El malvado usuario clica "Cancelar" o manda vacio.
                 if messagebox.askyesno("Salir", "¿Deseas salir del chat cancelando tu inicio?"):  # Aviso de salida definitiva
                     self.on_closing()
                     return
                 continue  # Si dice "No salir", lo regresamos al bucle AskString

            try:
                # Aquí viajan los Textos insertos hacia el back
                self.sock.sendall((username + "\n").encode())
                response = self.file.readline().strip()  # Lee reacción y respuesta de error al enviarlo.
            except Exception as e:
                 messagebox.showerror("Error", "Se perdió la conexión en autenticación.")
                 self.on_closing()
                 return
            
            # Condicional interceptor. Analiza el string response del server si rebotó...
            if "Username already taken" in response or "Username cannot be empty" in response:
                 # El servidor falló en procesar la alta. Lee la siguient line y reincertala al pop up y grita.
                 prompt = self.file.readline().strip()
                 messagebox.showwarning("Aviso Repetido", response)
            elif response.startswith("STATE:"):
                 # Milagro, Servidor nos arrojó la cadena cruda del ESTADO. Significa que accediste gloriosamente sin rechazos. 
                 self.username = username # Guardamos variable memoria para luego obviar ecos!
                 self.update_state_ui(response)  # Despachamos pintar el estado del server actual entrante en el Sidebar
                 self.display_message(f"✅ Conectado exitosamente y listo en nombre {username}", "center")
                 break  # FIN DEL TUTORIAL DE LOGEO - BREAK
            else:
                 # Flujo por defecto si repondió algun msg Random success genérico ("Hola bro" "Bienvenido")
                 self.username = username # Guardamos nuestro propio usuario variable general vital
                 self.display_message(f"✅ Conectado como {username}", "center")
                 self.display_message(response, "center")
                 break
        
        # Una vez logueados. Rompemos las cadenas bloqueadas y Deshabilitadas de input visual de los Widgets Bottom
        self.msg_entry.config(state='normal')
        self.send_btn.config(state='normal')
        self.msg_entry.focus_set()  # Auto clica visualmente el foco del raton al imput para no perder tiempo
        
        # Por último. Instala nuestro Centinela Asíncromo del tiempo (Thread). Su meta? Escuchar eternamente en segundo plano.
        self.running = True
        self.thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.thread.start()

    def update_state_ui(self, state_str):
        """Parseador de datos para refrescar la lista de usuarios. El servidor manda una macro cadena String."""
        # Formato de Cadena crudu: STATE:user1,user2|group1,group2
        try:
            data = state_str.split(":", 1)[1]  # Corta el prefijo STATE: para devolver solo puro listado alado -> "user1|group1"
            users_part, groups_part = data.split("|")  # Divide por la tubería '|' ambas entidades abstractas.
            
            # Convierte las listillas Strings planas y crudas a Arrays List de Python (Cortados limpios sacando la coma divisora)
            users = users_part.split(",") if users_part else [] 
            groups = groups_part.split(",") if groups_part else []

            # Manipulación pura de UI Listbox de Tkinter. Se borra su historial y pinta del End 0 a re-armar en base For loop fresquito
            self.users_listbox.delete(0, tk.END)
            for u in users:
               self.users_listbox.insert(tk.END, u)

            self.groups_listbox.delete(0, tk.END)
            for g in groups:
               self.groups_listbox.insert(tk.END, g)
        except Exception as e:
            pass  # Falla leve de parseo o desincronización, ignorar para proteger el App.

    def display_message(self, msg, tag="left", channel="Global"):
        """Inyectador Maestro a TextWidgets. Toma String, la canaliza a su pestaña adecuada y la tinta según el TAG de alineación CSS HTML-like."""
        self.create_tab(channel)  # Asegura 100% que adonde sea que va, no provoque un mega crasheo NoneType reference creando solapa
        
        # FILTRO DE REBOTE PROPIO (ECO): 
        # Si nuestra terminal local ya "DIBUJÓ" el mensaje que NOSOTROS mismsos tecleamos vía send_message...
        # Entonces cuando el SERVIDOR nos re-distribuya nuestro mismo texto back... esta IF evita repintarlo!
        if hasattr(self, 'username'):
            if msg.startswith(f"[{self.username}]") or msg.startswith(f"[# {channel[1:]}] {self.username}:"):
                return  # Rebota seco matando la funcion retorno de golpe (Ignorar)
                
        # SISTEMA DE NOTIFICACIÓN DE SOLAPAS:
        # Si el texto que llegó, corresponde a una solapa canal DIFERENTE en la que estamos posados...
        if channel != self.current_channel:
            tab_id = self.tabs[channel]["frame"]
            # Re-Bautizamos el Widget Superior pestaña TTK adosándole un Emojito Rojo '🔴'
            self.notebook.tab(tab_id, text=f" 🔴 {channel} ")

        # Obtiene finalmente el objeto mágico de la Caja de Textos Gigante 
        chat_area = self.tabs[channel]["text_area"]
        # Lo desencadena, habilita escritura (recordemos que de base estaba config:Disabled para que un humano no edite el Log viejo).
        chat_area.config(state='normal')
        
        # LA GLORIA TKINTER: Insert(END) adjunta una linea texto nuevo desde el fondo actual, metiendo ademas el TAG de estilo (Izquierda, Centro o Color Verde)
        chat_area.insert(tk.END, msg + "\n", tag)
        
        chat_area.see(tk.END)  # Obliga el Scroll de pantalla bajar agresivamente hasta abajo siguiendo los msgs frescos.
        chat_area.config(state='disabled')  # Reloquea para defenderse de edición manual de teclado humano sobre el área chat

    def receive_messages(self):
        """Bucle infinito principal que devora hilos... Se traga strings linea por linea entrante del Servidor Remoto."""
        try:
            for line in self.file:  # Bucle vivo por siempre
                if not self.running:
                    break  # Para salida segura
                    
                line = line.strip()  # Limpiar la entrada mugrosa de red.
                if not line:
                    continue  # Vacios fuera.

                # Set de variables Defaults
                channel = "Global"
                tag = "left"

                # DECODIFICADOR TEXTUAL PROTOCOLO: Adivinar por los brackets hacia donde va la onda.
                if line.startswith("[@ "):
                    # Entrante Privado! Formato: "[@ sender] text" -> Buscamos cortar y extraer extraños.
                    end_bracket = line.find("]")  # Encontrar índice de Cierre de bracket pos.
                    sender = line[3:end_bracket]  # Rebaña con SubString Slicing Py solo el alias ('sender')
                    channel = f"@{sender}"  # Etiqueta Canal de Destino local para Pestañería
                elif line.startswith("[# "):
                    # Entrante Grupal! Formato: "[# group] sender: text" 
                    end_bracket = line.find("]")
                    group = line[3:end_bracket]
                    channel = f"#{group}"

                elif line.startswith("[PM from "):
                    # Defensa histórica (Legacy PM de codigo roto anterior viejo)
                    end_bracket = line.find("]")
                    sender = line[9:end_bracket]
                    channel = f"@{sender}"
                elif line.startswith("[") and "] " in line:
                    # Entrante Global Chat!
                    pass  # Channel queda en "Global" var default asi que np.
                elif line.startswith("STATE:"):
                    # Process state broadcast (Barra lateral update list). En caso llegue fuera de tiempo
                    self.master.after(0, self.update_state_ui, line)  # Master After en 0s transpone la tarea asíncroma a la Ventana Grafica MAIN Loop (Por seguridad de UI Thread)
                    continue
                elif line.startswith("*") or line.startswith("Users:") or line.startswith("Server"):
                    # Si es sistema o mensaje rojizo sys...
                    tag = "center" # Cambia Alineación Tag hacia el Eje X central
                    
                # Despacha la orden final hacia la función dibujador de interface Grafica asegurado en thread primario por Master After 0ms timeout (Thread Safe Tkinter rules)
                self.master.after(0, self.display_message, line, tag, channel)
        except Exception:
            pass
        finally:
            if self.running:
                # Disconect abrupto desatado, dibuja alerta fatal al final
                self.master.after(0, self.display_message, "🔴 Falló grave y Desconectado del servidor.", "center", "Global")
                self.master.after(0, lambda: self.msg_entry.config(state='disabled'))  # Inhabilita botones input
                self.master.after(0, lambda: self.send_btn.config(state='disabled'))

    def send_message(self, event=None):
        """Disparador Manual del Entorno Grafico llamado al presionar ENTER o Click Btn"""
        msg = self.msg_entry.get().strip()  # Extrae valor actual de la cajita inferior de texto.
        if msg:
            try:
                # LÓGICA DE CONDICIONAL TÚNIZ PROTOCOLO: Dependiendo que pestaña focus tienes, enviará comando /gmsg /msg u normal
                if self.current_channel == "Global":
                    self.sock.sendall((msg + "\n").encode())  # Tiralo en string crudo
                    self.display_message(f"[Tú] {msg}", "right", "Global")  # Dibuja localmente de forma verde/derecha TÚ texto emitido 
                elif self.current_channel.startswith("@"):
                    target_user = self.current_channel[1:]  # Extrae al alias del man de la @ string
                    self.sock.sendall((f"/msg {target_user} {msg}\n").encode())  # Despacha parseado por Comando legado privado
                    self.display_message(f"[@ {target_user}] Tú: {msg}", "right", self.current_channel)
                elif self.current_channel.startswith("#"):
                    target_group = self.current_channel[1:]  # Extrae chat string room "#gatos" -> "gatos"
                    self.sock.sendall((f"/gmsg {target_group} {msg}\n").encode())  # Despacha al canal de grupo
                    self.display_message(f"[# {target_group}] Tú: {msg}", "right", self.current_channel)

                self.msg_entry.delete(0, tk.END)  # Limpieza post-envío borrando barra cuadro text para no ver texto colgado
            except Exception as e:
                self.display_message("🔴 Error al enviar mensaje por muerte conexion red.", "center", self.current_channel)

    def on_closing(self):
        """Handler Destructor y Limpiador protocolario al clickear la cruz roja SO OS X / Windows."""
        self.running = False  # Baja bandera mata-hilos asíncronos en while
        try:
            self.sock.close()  # Matar file descriptors C / Desconectar red
        except:
            pass
        self.master.destroy()  # Romper Instancia Tkinter
        sys.exit(0)  # Evaporar entorno virtual Python limpio y sin Errores


def main():
    """Definición Arranque matriz app Graphic"""
    root = tk.Tk()  # Invocar Genio ventana Tk base 
    app = ChatClientGUI(root)  # Encapsular dicha virgen enviandola dentro de tu Objeto Clase Constructor
    root.mainloop()  # Bloqueante Vital: La función mágica loop gráfica de GUI Tkinter que detiene código dibujando en vivo.

if __name__ == "__main__":
    main()
