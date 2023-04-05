import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { GearChoiceComponent } from './components/gear-choice/gear-choice.component';
import { AnchorChoiceComponent } from './components/anchor-choice/anchor-choice.component';
import { ClocksService } from './clocks.service';
import { HttpClientModule } from '@angular/common/http';
import { ClockPreviewComponent } from './components/clock-preview/clock-preview.component';
import { HandChoiceComponent } from './components/hand-choice/hand-choice.component';
import { FormsModule } from '@angular/forms';
import { DialChoiceComponent } from './components/dial-choice/dial-choice.component';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ClipboardModule } from '@angular/cdk/clipboard';

@NgModule({
  declarations: [
    AppComponent,
    GearChoiceComponent,
    AnchorChoiceComponent,
    ClockPreviewComponent,
    HandChoiceComponent,
    DialChoiceComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    FormsModule,
    NoopAnimationsModule,
    ClipboardModule
  ],
  providers: [ClocksService],
  bootstrap: [AppComponent]
})
export class AppModule { }
