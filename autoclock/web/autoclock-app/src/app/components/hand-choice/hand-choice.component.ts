import { Component } from '@angular/core';
import { ClocksService } from 'src/app/clocks.service';
import { HandStyle, HandStyle_list } from 'src/app/models/types';

@Component({
  selector: 'hand-choice',
  templateUrl: './hand-choice.component.html',
  styleUrls: ['./hand-choice.component.css']
})
export class HandChoiceComponent {

  public handStyle: HandStyle = HandStyle.SIMPLE_ROUND;
  public handStyles: HandStyle[] = HandStyle_list;
  public centredSecond: boolean = true;
  public centredSecondString: string = "_centred_seconds"
  public outline: boolean = true;
  public outlineString: string = "_with_outline"

  constructor(public clockService: ClocksService){
    clockService.setHands(this.handStyle, this.centredSecond, this.outline)
  }

  public chooseHandStyle(style: HandStyle){
    this.clockService.setHands(style, this.centredSecond, this.outline)
    this.handStyle = style
  }
  public chooseCentredSecond(centred: boolean){
    this.clockService.setHands(this.handStyle, centred, this.outline)
    this.centredSecond = centred
    this.centredSecondString = "";
    if (centred){
      this.centredSecondString = "_centred_seconds"
    }
  }
  public chooseOutline(outline: boolean){
    this.clockService.setHands(this.handStyle, this.centredSecond, outline)
    this.outline = outline
    this.outlineString = "";
    if (outline){
      this.outlineString = "_with_outline";
    }
  }

}
