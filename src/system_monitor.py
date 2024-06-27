import psutil
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive

class CPUWidget(Static):
    """A widget to display CPU information."""
    usage = reactive(0)
    temperature = reactive(None)
    fan_speed = reactive(None)

    def update_cpu(self):
        self.usage = psutil.cpu_percent()
        try:
            self.temperature = psutil.sensors_temperatures()['coretemp'][0].current
        except:
            self.temperature = None
        try:
            fans = psutil.sensors_fans()
            if fans:
                self.fan_speed = next(iter(fans.values()))[0].current
            else:
                self.fan_speed = None
        except:
            self.fan_speed = None

    def render(self):
        content = f"CPU Usage: {self.usage}%\n"
        if self.temperature:
            content += f"Temperature: {self.temperature:.1f}°C\n"
        if self.fan_speed:
            content += f"Fan Speed: {self.fan_speed} RPM"
        return content

class MemoryWidget(Static):
    """A widget to display memory information."""
    usage = reactive(0)
    used = reactive(0)
    total = reactive(0)

    def update_memory(self):
        memory = psutil.virtual_memory()
        self.usage = memory.percent
        self.used = memory.used / (1024 * 1024 * 1024)
        self.total = memory.total / (1024 * 1024 * 1024)

    def render(self):
        return f"Memory Usage: {self.usage:.1f}%\nUsed: {self.used:.1f} GB / Total: {self.total:.1f} GB"

class DiskWidget(Static):
    """A widget to display disk information."""
    usage = reactive(0)
    used = reactive(0)
    total = reactive(0)

    def update_disk(self):
        disk = psutil.disk_usage('/')
        self.usage = disk.percent
        self.used = disk.used / (1024 * 1024 * 1024)
        self.total = disk.total / (1024 * 1024 * 1024)

    def render(self):
        return f"Disk Usage: {self.usage:.1f}%\nUsed: {self.used:.1f} GB / Total: {self.total:.1f} GB"

class NetworkWidget(Static):
    """A widget to display network information."""
    sent = reactive(0)
    recv = reactive(0)

    def update_network(self):
        net_io = psutil.net_io_counters()
        self.sent = net_io.bytes_sent / (1024 * 1024)
        self.recv = net_io.bytes_recv / (1024 * 1024)

    def render(self):
        return f"Network Usage:\nSent: {self.sent:.2f} MB\nReceived: {self.recv:.2f} MB"

class ProcessesWidget(Static):
    """A widget to display top processes."""
    processes = reactive([])

    def update_processes(self):
        processes = []
        for process in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                # Get CPU percent with interval=None to avoid blocking
                cpu_percent = process.cpu_percent(interval=None)
                mem_percent = process.memory_percent()
                processes.append((process.pid, process.name(), cpu_percent, mem_percent))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Skip this process if we can't access its information
                continue
        
        # Sort processes by CPU usage
        processes.sort(key=lambda x: x[2], reverse=True)
        self.processes = processes[:5]  # Keep only top 5

    def render(self):
        table = "PID    Name                CPU%    Mem%\n"
        table += "-------------------------------------------\n"
        for pid, name, cpu, mem in self.processes:
            table += f"{pid:<6} {name:<20} {cpu:<7.1f} {mem:<7.1f}\n"
        return table

class SystemMonitorApp(App):
    """The main application class."""

    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(
            CPUWidget(),
            MemoryWidget(),
            DiskWidget(),
            NetworkWidget(),
            ProcessesWidget(),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Set up the application."""
        self.set_interval(1, self.update_data)

    def update_data(self) -> None:
        """Update the application data."""
        try:
            self.query_one(CPUWidget).update_cpu()
            self.query_one(MemoryWidget).update_memory()
            self.query_one(DiskWidget).update_disk()
            self.query_one(NetworkWidget).update_network()
            self.query_one(ProcessesWidget).update_processes()
        except Exception as e:
            print(f"Error updating data: {e}")

if __name__ == "__main__":
    app = SystemMonitorApp()
    app.run()