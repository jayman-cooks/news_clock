---
title: "RPI News clock"
author: "Jack (U0792RSM26A)"
description: "A rpi alarm clock that reads the news to me in the morning"
created_at: "6/22/2025"
---
## July 1 - 3.5h
I worked on trying to optimize the BOM, since I am currently above the $50 budget, but I think I can get it within. Originally, I bought a few things from adafruit. They had a shipping cost of six dollars, but I was able to find similarly priced items with free shipping (Vilros for rpi, aliexpress for small components). I also originally wanted to use a waveshare screen, even though I knew it would be expensive. The shipping was absurd though (\$15), and I would be paying half of my budget just to the screen. I was able to find another screen on aliexpress that did have good drawings, so I will remodel around that. Using the aliexpress screen will probably free up twenty dollars, so I will hopefully have room for a power supply, screw kit, and resistor kit. I also got chatgpt to write some code for it - its in main.py. 

## June 30 - 3h
Finished the case! My onshape rendering was bugging a bit so the colors might look a bit funny. Here's the final image:
![](https://github.com/jayman-cooks/news_clock/blob/main/full_final_case.jpg)
![](https://github.com/jayman-cooks/news_clock/blob/main/case_no_top.jpg)
One thing you cant see is how I mounted the screen. I have it bolt in to a bracket that is fixed to the bottom case with a press-fit peg. 
![](https://github.com/jayman-cooks/news_clock/blob/main/screen_stand1.jpg)
![](https://github.com/jayman-cooks/news_clock/blob/main/screen_stand2.jpg)
I wasn't really sure how to mount the buttons. I decided on just letting the button part of the buttons to slightly portrude, which requires a small cavity in the case for the rectangular part. The cavity will be filled with hot glue to fasten the buttons.  
![](https://github.com/jayman-cooks/news_clock/blob/main/buttons.jpg)

## June 25 - 3.5h
Worked on the case + did some research on components. I figured out I should use an rpi zero and a waveshare display(https://www.waveshare.com/product/displays/lcd-oled/lcd-oled-3/1.9inch-lcd-module.htm). Here's a picture of my whole case so far:
![alt text](https://github.com/jayman-cooks/news_clock/blob/main/body_1_rpi_news.jpg?raw=true)
I was trying to figure out how I would service the thing and work on it. I decided on making the bottom part removable, so I can slide it in and out. Here's the mechanism to do that:
![alt text](https://github.com/jayman-cooks/news_clock/blob/main/joining_mech_rpi_news.jpg?raw=true)
