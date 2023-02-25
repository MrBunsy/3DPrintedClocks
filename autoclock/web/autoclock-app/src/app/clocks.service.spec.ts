import { TestBed } from '@angular/core/testing';

import { ClocksService } from './clocks.service';

describe('ClocksService', () => {
  let service: ClocksService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ClocksService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
