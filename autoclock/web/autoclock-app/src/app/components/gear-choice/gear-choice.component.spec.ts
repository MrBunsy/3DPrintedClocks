import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GearChoiceComponent } from './gear-choice.component';

describe('GearChoiceComponent', () => {
  let component: GearChoiceComponent;
  let fixture: ComponentFixture<GearChoiceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ GearChoiceComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GearChoiceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
