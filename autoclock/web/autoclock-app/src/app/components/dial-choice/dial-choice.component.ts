import { Component, OnDestroy } from '@angular/core';
import { filter, map, Observable, pairwise, Subscription, tap } from 'rxjs';
import { ClocksService } from 'src/app/clocks.service';
import { Autoclock } from 'src/app/models/clock';
import { DialStyle, DialStyle_list } from 'src/app/models/types';

@Component({
  selector: 'dial-choice',
  templateUrl: './dial-choice.component.html',
  styleUrls: ['./dial-choice.component.css']
})
export class DialChoiceComponent implements OnDestroy {
  public hasDial: boolean = true;
  public dialStyle: DialStyle = DialStyle.LINES_ARC;
  public dialStyles : DialStyle[] = DialStyle_list;
  public loading: boolean = true;
  public clock$: Observable<Autoclock>;
  private subscription: Subscription;

  // //update when they're all supported
  // public secondsStyles: DialStyle[] = [DialStyle.LINES_ARC, DialStyle.CONCENTRIC_CIRCLES]
  public secondsStyle: DialStyle = DialStyle.CONCENTRIC_CIRCLES;

  constructor(public clockService: ClocksService){
    clockService.setDial(this.hasDial, this.dialStyle, this.secondsStyle);
    this.clock$ = clockService.getDialChanged();

    this.subscription = this.clock$.subscribe(clock => this.loading = true);
  }

  public chooseDial(hasDial: boolean){
    this.hasDial = hasDial;
    this.clockService.setDial(hasDial, this.dialStyle, this.secondsStyle);
  }

  public chooseStyle(style: DialStyle){
    this.dialStyle = style;
    this.clockService.setDial(this.hasDial, style, this.secondsStyle);
  }

  public chooseSecondsStyle(style: DialStyle){
    this.secondsStyle = style;
    this.clockService.setDial(this.hasDial, this.dialStyle, style);
  }

  public onLoad(){
    this.loading = false;
  }

  public ngOnDestroy() {
    this.subscription.unsubscribe()
  }
}
