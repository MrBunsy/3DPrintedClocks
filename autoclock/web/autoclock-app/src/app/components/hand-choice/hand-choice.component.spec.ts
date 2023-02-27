import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HandChoiceComponent } from './hand-choice.component';

describe('HandChoiceComponent', () => {
  let component: HandChoiceComponent;
  let fixture: ComponentFixture<HandChoiceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ HandChoiceComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HandChoiceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
