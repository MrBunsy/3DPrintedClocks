import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AnchorChoiceComponent } from './anchor-choice.component';

describe('AnchorChoiceComponent', () => {
  let component: AnchorChoiceComponent;
  let fixture: ComponentFixture<AnchorChoiceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AnchorChoiceComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AnchorChoiceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
