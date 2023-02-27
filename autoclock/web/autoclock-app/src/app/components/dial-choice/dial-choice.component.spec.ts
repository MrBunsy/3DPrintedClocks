import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DialChoiceComponent } from './dial-choice.component';

describe('DialChoiceComponent', () => {
  let component: DialChoiceComponent;
  let fixture: ComponentFixture<DialChoiceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DialChoiceComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DialChoiceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
