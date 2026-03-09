import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext
import sys

HOST = "127.0.0.1"
PORT = 5050

class ChatClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Computo Chat")
        self.master.geometry("500x600")
        self.master.configure(bg="#2E3440")
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file = None
        self.running = False

        self.setup_ui()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.master.after(100, self.connect_to_server)

    def setup_ui(self):
        self.bg_color = "#1E1E2E"
        self.sidebar_color = "#181825"
        self.panel_color = "#313244"
        self.text_color = "#CDD6F4"
        self.accent_color = "#89B4FA"
        self.accent_hover = "#B4BEFE"
        self.self_bubble = "#A6E3A1"
        self.other_bubble = "#89DCEB"
        self.system_text = "#F38BA8"

        self.master.geometry("800x600")
        self.master.configure(bg=self.bg_color)
        self.font_main = ("Helvetica", 14)
        self.font_bold = ("Helvetica", 14, "bold")
        self.font_small = ("Helvetica", 10, "italic")

        self.current_channel = "Global"
        self.tabs = {}

        from tkinter import ttk
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.sidebar_color, foreground=self.text_color, padding=[10, 5], font=self.font_bold)
        style.map("TNotebook.Tab", background=[("selected", self.panel_color)], foreground=[("selected", self.accent_color)])

        self.paned_window = tk.PanedWindow(self.master, orient=tk.HORIZONTAL, bg=self.bg_color, sashwidth=5, bd=0)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.sidebar_frame = tk.Frame(self.paned_window, bg=self.sidebar_color, width=200)
        self.paned_window.add(self.sidebar_frame, minsize=150)
        
        tk.Button(self.sidebar_frame, text="🌍 Global Chat", bg=self.panel_color, fg=self.text_color, borderwidth=0, command=lambda: self.switch_channel("Global")).pack(fill=tk.X, pady=5, padx=5)

        tk.Label(self.sidebar_frame, text="👥 Usuarios Conectados", bg=self.sidebar_color, fg=self.text_color, font=self.font_small).pack(fill=tk.X, pady=(10,0))
        self.users_listbox = tk.Listbox(self.sidebar_frame, bg=self.sidebar_color, fg=self.text_color, selectbackground=self.panel_color, borderwidth=0, highlightthickness=0)
        self.users_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.users_listbox.bind("<<ListboxSelect>>", self.on_user_select)

        tk.Label(self.sidebar_frame, text="💬 Grupos", bg=self.sidebar_color, fg=self.text_color, font=self.font_small).pack(fill=tk.X, pady=(10,0))
        self.groups_listbox = tk.Listbox(self.sidebar_frame, bg=self.sidebar_color, fg=self.text_color, selectbackground=self.panel_color, borderwidth=0, highlightthickness=0)
        self.groups_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.groups_listbox.bind("<<ListboxSelect>>", self.on_group_select)

        tk.Button(self.sidebar_frame, text="➕ Crear/Unirse Grupo", bg=self.panel_color, fg=self.text_color, borderwidth=0, command=self.prompt_group).pack(fill=tk.X, pady=5, padx=5)

        self.chat_frame = tk.Frame(self.paned_window, bg=self.bg_color)
        self.paned_window.add(self.chat_frame, minsize=400)

        self.notebook = ttk.Notebook(self.chat_frame)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.create_tab("Global")

        self.bottom_frame = tk.Frame(self.chat_frame, bg=self.panel_color, pady=10, padx=10)
        self.bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.entry_container = tk.Frame(self.bottom_frame, bg=self.panel_color)
        self.entry_container.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(10, 10))

        self.msg_entry = tk.Entry(
            self.entry_container,
            font=self.font_main, bg="#45475A", fg=self.text_color,
            insertbackground=self.text_color, borderwidth=0, highlightthickness=1,
            highlightcolor=self.accent_color, highlightbackground="#45475A"
        )
        self.msg_entry.pack(expand=True, fill=tk.X, ipady=12, padx=5, pady=5)
        self.msg_entry.bind("<Return>", self.send_message)
        
        self.send_btn = tk.Button(
            self.bottom_frame, text="Enviar ➔",
            font=self.font_bold, bg=self.accent_color, fg="#11111B",
            activebackground=self.accent_hover, borderwidth=0,
            cursor="hand2", command=self.send_message
        )
        self.send_btn.pack(side=tk.RIGHT, ipadx=15, ipady=8, padx=(0, 10))
        
        self.msg_entry.config(state='disabled')
        self.send_btn.config(state='disabled')

    def create_tab(self, channel_name):
        """Crea una nueva pestaña de chat si no existe."""
        if channel_name not in self.tabs:
            frame = tk.Frame(self.notebook, bg=self.bg_color)
            chat_area = scrolledtext.ScrolledText(
                frame, wrap=tk.WORD, state='disabled',
                bg=self.bg_color, fg=self.text_color,
                font=self.font_main, borderwidth=0, highlightthickness=0,
                padx=20, pady=20
            )
            chat_area.pack(expand=True, fill=tk.BOTH)
            
            chat_area.tag_config("right", justify="right", foreground=self.self_bubble)
            chat_area.tag_config("left", justify="left", foreground=self.other_bubble)
            chat_area.tag_config("center", justify="center", foreground=self.system_text, font=self.font_small)
            
            self.notebook.add(frame, text=f" {channel_name} ")
            self.tabs[channel_name] = {"frame": frame, "text_area": chat_area}

    def switch_channel(self, channel_name):
        self.current_channel = channel_name
        self.create_tab(channel_name)

        tab_id = self.tabs[channel_name]["frame"]
        self.notebook.select(tab_id)
        
        self.users_listbox.selection_clear(0, tk.END)
        self.groups_listbox.selection_clear(0, tk.END)

    def on_tab_changed(self, event):
        selected_tab = event.widget.select()
        if selected_tab:
            for channel_name, data in self.tabs.items():
                if str(data["frame"]) == selected_tab:
                    self.current_channel = channel_name
                    self.notebook.tab(selected_tab, text=f" {channel_name} ")
                    break

    def on_user_select(self, event):
        selection = event.widget.curselection()
        if selection:
            user = event.widget.get(selection[0])
            self.switch_channel(f"@{user}")

    def on_group_select(self, event):
        selection = event.widget.curselection()
        if selection:
            group = event.widget.get(selection[0])
            self.sock.sendall((f"/join {group}\n").encode())
            self.switch_channel(f"#{group}")

    def prompt_group(self):
        g_name = simpledialog.askstring("Grupo", "Nombre del grupo nuevo o a unirse (sin espacios):", parent=self.master)
        if g_name:
            self.sock.sendall((f"/creategroup {g_name}\n").encode())
            self.sock.sendall((f"/join {g_name}\n").encode())
            self.switch_channel(f"#{g_name}")

    def connect_to_server(self):
        try:
            self.sock.connect((HOST, PORT))
            self.file = self.sock.makefile("r")
        except Exception as e:
            messagebox.showerror("Error de conexión", f"No se pudo conectar al servidor:\n{e}")
            self.on_closing()
            return

        self.authenticate()

    def authenticate(self):
        try:
            prompt = self.file.readline().strip()
        except:
            messagebox.showerror("Error", "Desconectado del servidor")
            self.on_closing()
            return

        while True:
            username = simpledialog.askstring("Identificación", prompt, parent=self.master)
            if not username:
                 if messagebox.askyesno("Salir", "¿Deseas salir del chat?"):
                     self.on_closing()
                     return
                 continue

            try:
                self.sock.sendall((username + "\n").encode())
                response = self.file.readline().strip()
            except Exception as e:
                 messagebox.showerror("Error", "Se perdió la conexión.")
                 self.on_closing()
                 return
            
            if "Username already taken" in response or "Username cannot be empty" in response:
                 prompt = self.file.readline().strip()
                 messagebox.showwarning("Aviso", response)
            elif response.startswith("STATE:"):
                 self.username = username # Guardamos nuestro propio usuario
                 self.update_state_ui(response)
                 self.display_message(f"✅ Conectado como {username}", "center")
                 break
            else:
                 self.username = username # Guardamos nuestro propio usuario
                 self.display_message(f"✅ Conectado como {username}", "center")
                 self.display_message(response, "center")
                 break
        
        self.msg_entry.config(state='normal')
        self.send_btn.config(state='normal')
        self.msg_entry.focus_set()
        
        self.running = True
        self.thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.thread.start()

    def update_state_ui(self, state_str):
        try:
            data = state_str.split(":", 1)[1]
            users_part, groups_part = data.split("|")
            users = users_part.split(",") if users_part else []
            groups = groups_part.split(",") if groups_part else []

            self.users_listbox.delete(0, tk.END)
            for u in users:
               self.users_listbox.insert(tk.END, u)

            self.groups_listbox.delete(0, tk.END)
            for g in groups:
               self.groups_listbox.insert(tk.END, g)
        except Exception as e:
            pass

    def display_message(self, msg, tag="left", channel="Global"):
        self.create_tab(channel)

        if hasattr(self, 'username'):
            if msg.startswith(f"[{self.username}]") or msg.startswith(f"[# {channel[1:]}] {self.username}:"):
                return

        if channel != self.current_channel:
            tab_id = self.tabs[channel]["frame"]
            self.notebook.tab(tab_id, text=f" 🔴 {channel} ")

        chat_area = self.tabs[channel]["text_area"]
        chat_area.config(state='normal')
        chat_area.insert(tk.END, msg + "\n", tag)
        chat_area.see(tk.END)
        chat_area.config(state='disabled')

    def receive_messages(self):
        try:
            for line in self.file:
                if not self.running:
                    break
                line = line.strip()
                if not line:
                    continue

                channel = "Global"
                tag = "left"

                if line.startswith("[@ "):
                    end_bracket = line.find("]")
                    sender = line[3:end_bracket]
                    channel = f"@{sender}"
                elif line.startswith("[# "):
                    end_bracket = line.find("]")
                    group = line[3:end_bracket]
                    channel = f"#{group}"


                elif line.startswith("[PM from "):
                    end_bracket = line.find("]")
                    sender = line[9:end_bracket]
                    channel = f"@{sender}"
                elif line.startswith("[") and "] " in line:
                    pass
                elif line.startswith("STATE:"):
                    self.master.after(0, self.update_state_ui, line)
                    continue
                elif line.startswith("*") or line.startswith("Users:") or line.startswith("Server"):
                    tag = "center"

                self.master.after(0, self.display_message, line, tag, channel)
        except Exception:
            pass
        finally:
            if self.running:
                self.master.after(0, self.display_message, "🔴 Desconectado del servidor.", "center", "Global")
                self.master.after(0, lambda: self.msg_entry.config(state='disabled'))
                self.master.after(0, lambda: self.send_btn.config(state='disabled'))

    def send_message(self, event=None):
        msg = self.msg_entry.get().strip()
        if msg:
            try:
                if self.current_channel == "Global":
                    self.sock.sendall((msg + "\n").encode())
                    self.display_message(f"[Tú] {msg}", "right", "Global")
                elif self.current_channel.startswith("@"):
                    target_user = self.current_channel[1:]
                    self.sock.sendall((f"/msg {target_user} {msg}\n").encode())
                    self.display_message(f"[@ {target_user}] Tú: {msg}", "right", self.current_channel)
                elif self.current_channel.startswith("#"):
                    target_group = self.current_channel[1:]
                    self.sock.sendall((f"/gmsg {target_group} {msg}\n").encode())
                    self.display_message(f"[# {target_group}] Tú: {msg}", "right", self.current_channel)

                self.msg_entry.delete(0, tk.END)
            except Exception as e:
                self.display_message("🔴 Error al enviar mensaje.", "center", self.current_channel)

    def on_closing(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        self.master.destroy()
        sys.exit(0)

def main():
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
