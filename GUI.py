import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, scrolledtext
from threading import Thread

# --- Konfigurasi ---
BAUD_RATE = 115200

ser = None

def connect_serial():
    """Mencoba menghubungkan ke port serial."""
    global ser
    selected_port = port_combobox.get()
    if not selected_port:
        log_message("Pilih port terlebih dahulu!")
        return

    try:
        ser = serial.Serial(selected_port, BAUD_RATE, timeout=1)
        log_message(f"Berhasil terhubung ke {selected_port}")
        connect_button.config(text="Disconnect", command=disconnect_serial)
        port_combobox.config(state=tk.DISABLED)
        # Jalankan thread pembaca data agar GUI tidak macet
        Thread(target=read_from_port, daemon=True).start()
    except serial.SerialException as e:
        log_message(f"Gagal terhubung: {e}")
        log_message("Pastikan perangkat terhubung dan port sudah benar.")

def disconnect_serial():
    """Memutuskan koneksi serial."""
    global ser
    if ser and ser.is_open:
        ser.flush()
        ser.close()
        log_message("Koneksi terputus.")
    connect_button.config(text="Connect", command=connect_serial)
    port_combobox.config(state="readonly")

def send_command(command):
    """Mengirim perintah ke STM32 dengan newline."""
    global ser
    if ser and ser.is_open:
        full_command = (command + '\n').encode('utf-8')
        ser.reset_output_buffer() # Pastikan buffer bersih sebelum kirim
        ser.write(full_command)
        log_message(f"Kirim: {command}")
    else:
        log_message("Serial port tidak terhubung.")

def read_from_port():
    """Membaca data dari serial port secara terus-menerus."""
    global ser
    while ser and ser.is_open:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line: # Hanya log jika ada data
                log_message(f"Terima: {line}")
        except serial.SerialException:
            log_message("Koneksi terputus.")
            break
        except UnicodeDecodeError:
            pass

def log_message(message):
    """Menampilkan pesan di area log GUI."""
    log_area.config(state=tk.NORMAL)
    log_area.insert(tk.END, message + '\n')
    log_area.see(tk.END) # Auto-scroll
    log_area.config(state=tk.DISABLED)

root = tk.Tk()
root.title("STM32 LCD Control Panel")
root.geometry("500x550")

# --- Frame untuk Koneksi ---
connection_frame = ttk.LabelFrame(root, text="Koneksi Serial", padding=(10, 5))
connection_frame.pack(padx=10, pady=5, fill="x")

available_ports = [port.device for port in serial.tools.list_ports.comports()]
ttk.Label(connection_frame, text="Pilih Port:").pack(side=tk.LEFT, padx=(0, 5))
port_combobox = ttk.Combobox(connection_frame, values=available_ports, state="readonly")
if available_ports:
    port_combobox.set(available_ports[0])
port_combobox.pack(side=tk.LEFT, fill="x", expand=True)

connect_button = ttk.Button(connection_frame, text="Connect", command=connect_serial)
connect_button.pack(side=tk.LEFT, padx=(5, 0))

# --- Frame untuk Kontrol LCD ---
lcd_frame = ttk.LabelFrame(root, text="Kirim Teks ke LCD I2C", padding=(10, 5))
lcd_frame.pack(padx=10, pady=5, fill="x")

lcd_messages = [
    ("Tombol 1", "Halo Kelompok 4"),
    ("Tombol 2", "Hi Ganteng"),
    ("Tombol 3", "TRO JAYA JAYA")
]

for name, msg in lcd_messages:
    btn = ttk.Button(lcd_frame, text=f"Kirim '{msg}'", 
                     command=lambda m=msg: send_command(f"LCD:{m}"))
    btn.pack(pady=2, fill="x")

# --- Frame untuk Log Komunikasi ---
log_frame = ttk.LabelFrame(root, text="Log Komunikasi", padding=(10, 5))
log_frame.pack(padx=10, pady=5, fill="both", expand=True)

log_area = scrolledtext.ScrolledText(log_frame, state=tk.DISABLED, height=10, wrap=tk.WORD)
log_area.pack(fill="both", expand=True)

def on_closing():
    disconnect_serial()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()