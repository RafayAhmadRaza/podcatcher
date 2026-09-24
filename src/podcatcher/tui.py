from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Header, Footer,ListItem,ListView
from .database import get_podcasts

podcasts = get_podcasts()

SELECTED_PDC = 0

class PodcatcherApp(App):
    CSS_PATH = "tui.tcss"
    def on_list_view_selected(self,event: ListView.Selected):
        global SELECTED_PDC
        message = self.query_one("#message",Static)
        message.update(f"Selected: {event.index}")
        SELECTED_PDC = event.index
        episodes_list = self.query_one("#episodes-list",ListView)
        episodes_list.clear()
        pdc = podcasts[SELECTED_PDC]

        for ep in pdc.episodes:
            episodes_list.append(ListItem(Static(ep.title)))

    def compose(self) -> ComposeResult:
        global SELECTED_PDC

        yield Header(show_clock = True, name="Podcatcher", id="header")
        with Horizontal():
            with Vertical(id="podcasts"):
                 with ListView(id="podcast-list"):
                    for pdc in podcasts:
                        yield ListItem(Static(pdc.title))
                
            with Vertical(id="episodes"):
                with ListView(id="episodes-list"):
                    pdc = podcasts[SELECTED_PDC]
                    for ep in pdc.episodes:
                            yield ListItem(Static(ep.title))

        yield Static("Waiting for selection...", id="message")

        yield Footer(name="Footer",id="footer")

if __name__ == "__main__":
    app = PodcatcherApp()

    app.run()