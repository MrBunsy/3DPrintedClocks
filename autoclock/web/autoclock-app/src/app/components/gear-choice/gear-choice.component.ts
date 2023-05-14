import { Component } from '@angular/core';
import { ClocksService } from 'src/app/clocks.service';
import { GearStyle, GearStyle_list } from 'src/app/models/types';

let ignoreGears = [GearStyle.CIRCLES_HOLLOW, GearStyle.TREE, GearStyle.MOONS]

@Component({
  selector: 'gear-choice',
  templateUrl: './gear-choice.component.html',
  styleUrls: ['./gear-choice.component.css']
})
export class GearChoiceComponent {
  public gears: GearStyle[] = GearStyle_list.filter(element => ignoreGears.indexOf(element) < 0)
  public chosenGear: GearStyle = GearStyle.ARCS

  constructor(public clockService: ClocksService){
      clockService.setGear(this.chosenGear)
  }

  public chooseGear(gear: GearStyle){
    this.chosenGear = gear;
    this.clockService.setGear(gear)
  }

 

}
