import { AnchorStyle, DialStyle, EscapementType, GearStyle, HandStyle } from "./types";

export class Autoclock{
    /**
     * to mirror autoclock in python
     * @param escapement 
     * @param gear_style 
     * @param anchor_style 
     * @param pendulum_period_s 
     * @param days 
     * @param centred_second_hand 
     * @param has_dial 
     * @param dial_style 
     * @param dial_seconds_style 
     * @param hand_style 
     * @param hand_has_outline 
     */
    constructor(public escapement: EscapementType = EscapementType.DEADBEAT,
         public gear_style: GearStyle = GearStyle.ARCS,
         public anchor_style: AnchorStyle = AnchorStyle.STRAIGHT,
         public pendulum_period_s: number=2,
         public days:number=8,
         public centred_second_hand:boolean=false,
         public has_dial: boolean=false,
         public dial_style: DialStyle = DialStyle.LINES_ARC,
         public dial_seconds_style: DialStyle = DialStyle.LINES_ARC,
         public hand_style: HandStyle = HandStyle.SIMPLE_ROUND,
         public hand_has_outline:boolean=true){

    }

    public getName(): string{
        /**
         * Should match the logic in Autoclock constructor
         */
        let dial_style_string = ""
        if (this.has_dial){
            dial_style_string = "_" + this.dial_style
            if (this.dial_seconds_style.length > 0 && (this.pendulum_period_s == 2 || this.pendulum_period_s == 1.5))
                dial_style_string += "_" + this.dial_seconds_style
        }
        let dial = "nodial";
        if (this.has_dial){
            dial = "dial";
        }
        let centred_second = "";
        if (this.centred_second_hand){
            centred_second = "centred_second"
        }
        return `autoclock_${this.pendulum_period_s}s_${this.days}day${centred_second}_${dial}${dial_style_string}_${this.gear_style}_${this.anchor_style}_${this.hand_style}`
    }
}