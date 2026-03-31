# C++ Bugs in SplashKit Online

This document records issues found while testing C++ in SplashKit Online.

## Test Format

For each issue:
- Feature tested
- Sample code, files or function used
- Expected result
- Actual result
- Errors or compiler output
- Notes

---

## Bug 1:

**Feature tested:**
Multi-file C++ project with a user-defined header file

**Files used:**
`main.cpp`, `game.h`, `game.cpp`

**Sample code:**

`main.cpp`
```cpp
#include "splashkit.h"
#include "game.h"

int main()
{
    open_window("Header Test", 800, 600);

    while (!quit_requested())
    {
        process_events();
        clear_screen(COLOR_WHITE);

        draw_scene();

        refresh_screen(60);
    }

    return 0;
}
```

`game.h`
```cpp
#ifndef GAME_H
#define GAME_H

#include "splashkit.h"

void draw_scene();

#endif
```

`game.cpp`
```cpp
#include "game.h"

void draw_scene()
{
    fill_circle(COLOR_RED, 400, 300, 50);
}
```

**Expected result:**
The program should compile and run, displaying a red circle in the window.

**Actual result:**
Compilation fails when splashkit.h is included through game.h.

**Compiler output:**
In file included from /code/main.cpp:2:
In file included from /code/game.h:4:
In file included from /include/splashkit.h:16:
/include/splashkit/bundles.h:139:1: error: extraneous closing brace ('}')
}
^
In file included from /code/main.cpp:2:
In file included from /code/game.h:4:
In file included from /include/splashkit.h:17:
/include/splashkit/interface.h:810:1: error: extraneous closing brace ('}')
}
^
In file included from /code/main.cpp:2:
In file included from /code/game.h:4:
In file included from /include/splashkit.h:25:
/include/splashkit/camera.h:335:1: error: extraneous closing brace ('}')
}
^
In file included from /code/main.cpp:2:
In file included from /code/game.h:4:
In file included from /include/splashkit.h:26:
/include/splashkit/random.h:47:1: error: extraneous closing brace ('}')
}
^
4 errors generated.

**Notes:**
A basic single file C++ program including splashkit.h directly in main.cpp compiled and ran successfully.
The error only appeared after introducing a separate header file (game.h) that includes splashkit.h.
I tested the same multi file program removing splashkit.h from the separate header file (game.h) and it compiled and ran successfully.
This suggests an issue with header handling, include order, or malformed C++ headers in SplashKit Online.