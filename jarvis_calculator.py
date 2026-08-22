import tkinter as tk
from tkinter import messagebox

class JarvisCalculator:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Jarvis Calculator")
        self.entry = tk.Entry(self.window)
        self.entry.grid(row=0, column=0, columnspan=4)
        self.button1 = tk.Button(self.window, text="2", command=lambda: self.append_to_entry("2"))
        self.button1.grid(row=1, column=0)
        self.button2 = tk.Button(self.window, text="3", command=lambda: self.append_to_entry("3"))
        self.button2.grid(row=1, column=1)
        self.button3 = tk.Button(self.window, text="