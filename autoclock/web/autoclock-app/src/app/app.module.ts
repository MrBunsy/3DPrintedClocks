import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { GearChoiceComponent } from './components/gear-choice/gear-choice.component';

@NgModule({
  declarations: [
    AppComponent,
    GearChoiceComponent
  ],
  imports: [
    BrowserModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
