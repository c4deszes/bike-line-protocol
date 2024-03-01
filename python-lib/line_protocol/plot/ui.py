import customtkinter
from tkinter import messagebox
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from threading import Thread
import serial.tools.list_ports

import logging

from line_protocol.monitor.config import load_config, MonitoringConfig
from line_protocol.monitor.traffic import TrafficLogger
from line_protocol.monitor.measurement import Measurement, TimeSeries, DataPoint
from line_protocol.protocol.master import LineMaster
from line_protocol.protocol.transport import LineSerialTransport

# link: https://www.youtube.com/watch?v=0V-6pu1Gyp8

class MeasurementContext:
    started: bool
    config: MonitoringConfig
    transport: LineSerialTransport
    master: LineMaster
    traffic_logger: TrafficLogger
    measurement: Measurement

    # Internal UI state
    lastTrafficIndex: int
    axis: dict

    def run(self):
        for schedule in self.config.preStartSchedules:
            schedule.perform(self.master)

        while self.started:
            self.config.mainSchedule.perform(self.master)

class App(customtkinter.CTk):

    def __init__(self):
        super().__init__()

        logging.basicConfig(level=logging.DEBUG)

        # Window settings
        self.title("my app")
        self.geometry("800x800")
        self.grid_columnconfigure((0), weight=1)
        self.grid_rowconfigure((1), weight=10)
        self.grid_rowconfigure((2), weight=2)

        frame_ConfigPanel = customtkinter.CTkFrame(self)
        frame_ConfigPanel.grid(row=0, column=0, columnspan=2, sticky='nesw')

        ports = serial.tools.list_ports.comports()

        self.combo_PortSelect = customtkinter.CTkComboBox(frame_ConfigPanel, values=[x.device for x in ports])
        self.combo_PortSelect.grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.checkbox_MasterMode = customtkinter.CTkCheckBox(frame_ConfigPanel, text='Master')
        self.checkbox_MasterMode.grid(row=0, column=1, padx=10, pady=10, sticky='e')

        self.text_ConfigFile = customtkinter.CTkLabel(frame_ConfigPanel, text='config.json')
        self.text_ConfigFile.grid(row=0, column=2, padx=10, pady=10)
        self.button_ConfigFileSelect = customtkinter.CTkButton(frame_ConfigPanel, text='Select', command=self.select_config)
        self.button_ConfigFileSelect.grid(row=0, column=3, padx=10, pady=10)

        self.button_CaptureStart = customtkinter.CTkButton(frame_ConfigPanel, text='Start', width=10, command=self.start_measurement)
        self.button_CaptureStart.grid(row=0, column=4, padx=10, pady=10)

        self.button_CaptureStop = customtkinter.CTkButton(frame_ConfigPanel, text='Stop', width=10, state='disabled', command=self.stop_measurement)
        self.button_CaptureStop.grid(row=0, column=5, padx=10, pady=10)

        frame_ConfigPanel.grid_columnconfigure((0, 1), weight=0)
        frame_ConfigPanel.grid_columnconfigure((2, 3), weight=5)
        frame_ConfigPanel.grid_columnconfigure((4, 5), weight=0)

        self.scroll_Plots = customtkinter.CTkScrollableFrame(self)
        self.scroll_Plots.grid(row=1, column=0, padx=10, pady=10, sticky='nesw')
        self.scroll_Plots.columnconfigure(0, weight=1)
        self.scroll_Plots.rowconfigure(0, weight=1)

        frame_Traffic = customtkinter.CTkFrame(self)
        frame_Traffic.grid(row=1, column=1, padx=10, pady=10, sticky='nesw')

        self.list_TrafficEntries = ttk.Treeview(frame_Traffic, columns=('timestamp', 'request', 'data'), show='headings')
        self.list_TrafficEntries.heading('timestamp', text='Time')
        self.list_TrafficEntries.heading('request', text='ID')
        self.list_TrafficEntries.heading('data', text='Message')
        self.list_TrafficEntries.column('timestamp', width=60, stretch=False)
        self.list_TrafficEntries.column('request', width=50, stretch=False)
        self.list_TrafficEntries.column('data', width=200, stretch=True)
        self.list_TrafficEntries.grid(row=0, column=0, padx=10, pady=10, sticky='nesw')
        scrollbar = customtkinter.CTkScrollbar(frame_Traffic, command=self.list_TrafficEntries.yview)
        self.list_TrafficEntries.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
        frame_Traffic.columnconfigure(0, weight=1)
        frame_Traffic.rowconfigure(0, weight=1)

        frame_Logs = customtkinter.CTkFrame(self)
        frame_Logs.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='nesw')

        # self.button = customtkinter.CTkButton(self, text="my button", command=self.button_callback)
        # self.button.grid(row=0, column=0, padx=20, pady=20, sticky="ew", columnspan=2)
        # self.checkbox_1 = customtkinter.CTkCheckBox(self, text="checkbox 1")
        # self.checkbox_1.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")
        # self.checkbox_2 = customtkinter.CTkCheckBox(self, text="checkbox 2")
        # self.checkbox_2.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="w")

        self.protocol('WM_DELETE_WINDOW', self.on_window_close)

        self.measurement = MeasurementContext()
        self.measurement.started = False
        self.measurement.lastTrafficIndex = 0

    def on_window_close(self):
        if self.measurement.started:
            if messagebox.askokcancel('Quit', 'A measurement is running, are you sure you want to quit?'):
                self.stop_measurement()
                self.destroy()
        else:
            self.destroy()

    def select_config(self):
        self.config_path = customtkinter.filedialog.askopenfilename(filetypes=[('Network JSON', 'json')])
        self.text_ConfigFile.configure(require_redraw=True, text=self.config_path)

    def start_measurement(self):
        self.measurement.config = load_config(self.config_path)
        self.measurement.axis = {}

        for widget in self.scroll_Plots.winfo_children():
            widget.destroy()
        self.setup_plots()

        if self.checkbox_MasterMode.get() == 1:
            # setup LineMaster, load config, etc.
            self.measurement.transport = LineSerialTransport(self.combo_PortSelect.get(), self.measurement.config.network.baudrate, one_wire=True)
            self.measurement.master = LineMaster(self.measurement.transport, self.measurement.config.network)
            self.measurement.traffic_logger = TrafficLogger()
            self.measurement.measurement = Measurement()
            self.measurement.transport.add_listener(self.measurement.traffic_logger)
            self.measurement.master.add_listener(self.measurement.measurement)
            self.measurement.transport.__enter__()
        else:
            # setup LineListener, load config
            pass

        self.measurement.lastTrafficIndex = 0
        self.measurement.started = True
        self.measurement_thread = Thread(target=self.measurement.run)
        self.measurement_thread.start()

        # TODO: only disable on success
        self.button_CaptureStart.configure(state='disabled')
        self.button_CaptureStop.configure(state='normal')
        self.checkbox_MasterMode.configure(state='disabled')
        self.button_ConfigFileSelect.configure(state='disabled')
        self.combo_PortSelect.configure(state='disabled')

    def stop_measurement(self):
        self.measurement.started = False
        self.measurement_thread.join(10)

        self.measurement.transport.__exit__(None, None, None)

        self.button_CaptureStart.configure(state='normal')
        self.button_CaptureStop.configure(state='disabled')
        self.checkbox_MasterMode.configure(state='normal')
        self.button_ConfigFileSelect.configure(state='normal')
        self.combo_PortSelect.configure(state='normal')
        pass

    def setup_plots(self):
        figure = Figure()

        for (i, plot) in enumerate(self.measurement.config.plots):
            ax = figure.add_subplot(len(self.measurement.config.plots), 1, i+1)
            ax.set_title(plot.name)
            ax.set_xlabel('Time')
            #ax.set_xlim(0, 10)
            self.measurement.axis[plot.name] = {
                'axis': ax,
                'signals': {}
            }
            for signal in plot.signals:
                self.measurement.axis[plot.name]['signals'][signal] = ax.plot([], [])[0]

        self.canvas = FigureCanvasTkAgg(figure, master=self.scroll_Plots)
        self.canvas.get_tk_widget().grid(row=0, column=0, padx=10, pady=10, sticky='nesw')
        self.canvas.draw()

    def update_ui(self):
        self.update_traffic()
        self.update_plots()

        self.after(10, self.update_ui)

    def update_plots(self):
        if hasattr(self, 'canvas'):
            for plot in self.measurement.config.plots:
                for signal in plot.signals:
                    if signal in self.measurement.measurement.data:
                        timestamps = [v.timestamp for v in self.measurement.measurement.data[signal].data]
                        values = [v.value for v in self.measurement.measurement.data[signal].data]
                        self.measurement.axis[plot.name]['signals'][signal].set_data(timestamps, values)
                self.measurement.axis[plot.name]['axis'].relim()
                self.measurement.axis[plot.name]['axis'].autoscale_view()
            self.canvas.draw()
            self.canvas.flush_events()

    def update_traffic(self):
        if hasattr(self.measurement, 'traffic_logger') and self.measurement.traffic_logger.has_changed():
            lastIndex = len(self.measurement.traffic_logger.traffic.logs)
            for entry in self.measurement.traffic_logger.traffic.logs[self.measurement.lastTrafficIndex:lastIndex]:
                item = self.list_TrafficEntries.insert('', customtkinter.END, values=(f"{entry.timestamp:.03f}", f"0x{entry.request:04X}", str(entry)))
                # TODO: conditional autoscroll
                self.list_TrafficEntries.see(item)
            self.measurement.lastTrafficIndex = lastIndex

    def open_configuration(self):
        print("button pressed")

def main():
    app = App()
    app.after(10, app.update_ui)
    app.mainloop()

    return 0

if __name__ == '__main__':
    main()
