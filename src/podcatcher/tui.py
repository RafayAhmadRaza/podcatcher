from podcatcher.player import start_play
from podcatcher.player import create_player
from textual.app import App, ComposeResult
from textual import events, timer
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Header, Footer,ListItem,ListView,ProgressBar
from .database import get_podcasts
from .player import *
podcasts = get_podcasts()

SELECTED_PDC = 0

class PodcatcherApp(App):
    CSS_PATH = "tui.tcss"
    def on_key(self,event: events.Key) -> None:
        if event.key == "left":
            message = self.query_one("#message",Static)
            message.update(f"Selected: j")
            podcasts_list = self.query_one("#podcast-list")
            podcasts_list.focus()
        if event.key == "right":
            
            message = self.query_one("#message",Static)
            message.update(f"Selected: l")
            ep_list = self.query_one("#episodes-list")
            ep_list.focus()

    def update_player_time(self):
        time_started, total_length = get_timer(self.current_player)

        time_started_secs = time_started // 1000
        total_length_secs = total_length // 1000

        if total_length_secs <= 0:
            return

        ts_mins, ts_secs = divmod(time_started_secs, 60)
        tl_mins, tl_secs = divmod(total_length_secs, 60)

        message = self.query_one("#message", Static)
        message.update(
            f"{ts_mins:02}:{ts_secs:02} / {tl_mins:02}:{tl_secs:02}"
        )

        progress = self.query_one("#progress", ProgressBar)
        progress.update(
            progress=(time_started_secs / total_length_secs) * 100
        )
            
            
            
            
                    
        
    def on_list_view_selected(self,event: ListView.Selected):
      
        podcast_list = self.query_one("#podcast-list",ListView)
        episodes_list = self.query_one("#episodes-list",ListView)
        global SELECTED_PDC

        if event.list_view == podcast_list:

            episodes_list = self.query_one("#episodes-list",ListView)
        
            
            SELECTED_PDC = event.index
            
            
            episodes_list.clear()
            
            pdc = podcasts[SELECTED_PDC]

            for ep in pdc.episodes:
                episodes_list.append(ListItem(Static(ep.title)))
        
        if event.list_view == episodes_list:
            pdc = podcasts[SELECTED_PDC]

            ep_index = event.index
            
            ep = pdc.episodes[ep_index]

            if ep.is_downloaded:
                
                if ep.local_path:
                    message = self.query_one("#message",Static)
                    message.update(f"True")

                    self.current_player = create_player(pdc.id,ep)

                    start_play(self.current_player)
                    
                    timeStarted,total_lenght = get_timer(self.current_player)

                    timeStarted_secs = timeStarted//1000
                    
                    total_lenght_secs = total_lenght//1000

                    TS_mins, TS_secs = divmod(timeStarted_secs,60)
                    TL_mins, TL_secs = divmod(total_lenght_secs,60)


                    self.set_interval(1,self.update_player_time)
             
             
                    message = self.query_one("#message",Static)
             

                    message.update(f"{TS_mins:02}:{TS_secs:02} / {TL_mins:02}:{TL_secs:02}")
                    
                    progress = self.query_one("#progress", ProgressBar)
                    progress.update(progress=0)
            
            
            
            
            
            
            
            if not ep.is_downloaded:
                if ep.audio_url:

                    message = self.query_one("#message",Static)
                    message.update(f" audio url exist True")

                    self.current_player = create_network_player(pdc.id,ep)

                    start_play(self.current_player)
                    
                    timeStarted,total_lenght = get_timer(self.current_player)

                    timeStarted_secs = timeStarted//1000
                    
                    total_lenght_secs = total_lenght//1000

                    TS_mins, TS_secs = divmod(timeStarted_secs,60)
                    TL_mins, TL_secs = divmod(total_lenght_secs,60)


                    self.set_interval(1,self.update_player_time)
             
             
                    message = self.query_one("#message",Static)
             

                    message.update(f"{TS_mins:02}:{TS_secs:02} / {TL_mins:02}:{TL_secs:02}")
                    
                    progress = self.query_one("#progress", ProgressBar)
                    progress.update(progress=0)
            
            
            
            


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
        yield ProgressBar(total=100,id='progress')

        yield Static("Waiting for selection...", id="message")

        yield Footer(name="Footer",id="footer")

if __name__ == "__main__":
    app = PodcatcherApp()

    app.run()