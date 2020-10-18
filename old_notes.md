## Performance Tweaks
Kodi can sometimes have problems playing content on very changable network links. By using some settings from http://kodi.wiki/view/HOW-TO:Modify_the_video_cache. This can be fixed to get Kodi to download as much buffer as fast as possible to prevent stalling of playback.

Add the following options inbetween the `<advancedsettings></advancedsettings>` tag in the `advancedsettings.xml` settings file.
```
<cache>
  <memorysize>524288000</memorysize>
  <readfactor>20.0</readfactor>
</cache>
```
memorysize is set to 500MB, this will cause Kodi to buffer up to 500MB of video in RAM. Note that Kodi will require 3x this value so this setting this to 500MB will make Kodi use at least 1.5GB of RAM.
readfactor is set to 20 (over the default of 4). The author found that when the network dropped the buffer would disappear and as the readfactor wasn't high enough Kodi wouldn't be able to refill the buffer in the times when there was spare bandwidth. As a result the buffer would gradually deplete until it was empty and Kodi continually had to stop to fill up the buffer.
