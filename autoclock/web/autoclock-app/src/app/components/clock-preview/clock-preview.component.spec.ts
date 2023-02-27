import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ClockPreviewComponent } from './clock-preview.component';

describe('ClockPreviewComponent', () => {
  let component: ClockPreviewComponent;
  let fixture: ComponentFixture<ClockPreviewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ClockPreviewComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ClockPreviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
