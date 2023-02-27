import { Component, OnDestroy, OnInit } from '@angular/core';
import { Observable, Subscription } from 'rxjs';
import { ClocksService } from 'src/app/clocks.service';
import { Autoclock } from 'src/app/models/clock';

@Component({
  selector: 'clock-preview',
  templateUrl: './clock-preview.component.html',
  styleUrls: ['./clock-preview.component.css']
})
export class ClockPreviewComponent implements OnDestroy {
  public clock$: Observable<Autoclock>
  private subscription: Subscription;

  public show: boolean = false;
  public loading: boolean = true;

  constructor(public clockService: ClocksService){
    this.clock$ = clockService.getClock()

    this.subscription = this.clock$.subscribe(clock => this.show = false);
  }

  public generateClock(){
    this.show = true;
    this.loading = true;
  }

public onLoad(){
  this.loading = false;
}

  ngOnDestroy() {
    this.subscription.unsubscribe()
  }
}
