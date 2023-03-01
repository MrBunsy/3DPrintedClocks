import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { AnchorStyle, DialStyle, GearStyle, HandStyle } from './models/types';
import { Observable, ReplaySubject, Subject } from 'rxjs';
import { Autoclock } from './models/clock';

@Injectable({
  providedIn: 'root'
})
export class ClocksService {

  /**
   * This is for tracking the clock currently being configured, it will provide the remaining options that can be configured based on previous selections
   * and previews from python
   * @param http 
   */

  private clockSubject: ReplaySubject<Autoclock>;
  private clock: Autoclock
  private dialChanged: Subject<Autoclock>;

  constructor(private http: HttpClient) {
    this.clockSubject = new ReplaySubject<Autoclock>();
    this.clock = new Autoclock()
    this.dialChanged = new ReplaySubject<Autoclock>();

    this.dialChanged.next(this.clock);
    this.clockSubject.next(this.clock);
   }

   public getClock(): Observable<Autoclock>{
      return this.clockSubject.asObservable()
   }

   /**
    * Emits if the dial or hands (to create a dial preview) have changed
    * @returns 
    */
   public getDialChanged(): Observable<Autoclock>{
     return this.dialChanged.asObservable();
   }

   public setGear(gear: GearStyle){
    this.clock.gear_style = gear
    this.clockSubject.next(this.clock)
   }
   
   public setAnchorStyle(anchorStyle: AnchorStyle){
    this.clock.anchor_style = anchorStyle
    this.clockSubject.next(this.clock)
  }
  
  public setHands(style: HandStyle, centredSecond: boolean, outline: boolean){
    this.clock.hand_style = style
    this.clock.hand_has_outline = outline;
    this.clock.centred_second_hand = centredSecond
    this.clockSubject.next(this.clock)
    this.dialChanged.next(this.clock);
  }

  public setDial(hasDial: boolean, style: DialStyle, secondsStyle: DialStyle){
    this.clock.has_dial = hasDial;
    this.clock.dial_style = style;
    this.clock.dial_seconds_style = secondsStyle;
    this.clockSubject.next(this.clock);
    this.dialChanged.next(this.clock);
  }
}
