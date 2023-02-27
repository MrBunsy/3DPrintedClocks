import { Component } from '@angular/core';
import { ClocksService } from 'src/app/clocks.service';
import { AnchorStyle, AnchorStyle_list } from 'src/app/models/types';

@Component({
  selector: 'anchor-choice',
  templateUrl: './anchor-choice.component.html',
  styleUrls: ['./anchor-choice.component.css']
})
export class AnchorChoiceComponent {

  public anchors: AnchorStyle[] = AnchorStyle_list;
  public anchor: AnchorStyle = AnchorStyle.CURVED_MATCHING_WHEEL;

  constructor(public clockService: ClocksService){
    clockService.setAnchorStyle(this.anchor)
  }

  public chooseAnchorStyle(anchorStyle: AnchorStyle){
    this.anchor = anchorStyle
    this.clockService.setAnchorStyle(anchorStyle)
  }
}
