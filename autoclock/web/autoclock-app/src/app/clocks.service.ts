import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ClocksService {

  /**
   * This is for tracking the clock currently being configured, it will provide the remaining options that can be configured based on previous selections
   * and previews from python
   * @param http 
   */
  constructor(private http: HttpClient) {
    
   }


  public get
}
