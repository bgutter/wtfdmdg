# wtfdmdg
Where did my day go? This keyboard-driven Python/QT application will help you unobtrusively track your time and visualize the answer to that question.

# Disclaimer

This project is unmaintained in the sense that I no longer use it, and won't be adding new features. I switched to org-mode some time ago. However, it does generally work well, and did precisely what I needed for time tracking 2 years ago.

You may run into some bugs. Feel free to submit bug reports or pull-requests if you find this useful.

# Basic Tasking Tutorial

![UI](ss.png?raw=true "wtfdmdg UI")

Wtfdmdg essentially maintains a list of tasks. Tasks represent the things that you do which take time out of your day. They can be things you've done, are doing, or will do.

## Task Attributes and Command Syntax

All interaction occurs through the syntax-highlighted command box. Each command can have up to 4 parameters, corresponding to the 4 parts of each task.
* reference number (shown in black)
* start time (shown in blue)
* end time (shown in yellow)
* body (shown in red)

The format, in its fullest form, is as follows:
```
{ref}:{start}-{end}.{body}
```

An example of a fully formed command, with no omitted fields, would be something like:
```
3:0330-1221.In meetings about staple project
```

In this example:
* 3 is the reference number
* 3:30 is the start time
* 12:21 is the end time (always using 24-hour time)
* "In meetings about staple project" is the body

In effect, this command will set the start time, end time, and body for the *task* with reference number 3.
* Reference number is unambiguously terminated with a colon (":")
* Start time is unambiguously terminated with a dash ("-")
* End time is unambiguously terminated with a period (".")

Note that the command parser is quite forgiving, and delimiters can often be omitted. Because times contain only digits (with one exception mentioned below), you can often omit the period between end-time and the task body. The colon after the reference number is quite similar.

## Creating Tasks

You won't, of course, have any tasks when you first start the program. To create a new task, just *omit the reference number.*

```
0330-1221.In meetings about the staple project
```

A reference number will always be generated. Other fields can also be omitted when creating a new task -- in fact, they will *usually* be omitted.

```
0330-In meetings about the staple project
```

This creates a new task with the given body, a newly generated reference number, and given start time. It will have no end time. This is considered an active task -- it is something you are currently working on.

## Closing Tasks

Now, let's assume that the task created in the last code block was given a reference number of 5. What if we want to close the task? Let's assume the task ended at 4:00. To do this, just type a command with an explicit reference number (5), and an explicit end time. For existing tasks, *omitted fields are ignored, and included fields overwrite*.

```
5:-4
```

Now, all fields for task 5 will be filled, and it will be 'closed'.

## Time Parsing

Time parsing is flexible, and wtfdmdg tries to make the most reasonable assumptions about what you mean. Again, it strictly uses 24-hour times.

* 1 means 1:00
* 10 means 10:00
* 130 means 1:30
* 1300 means 13:00
* 1921 means 19:21

Generally, one or two digits is assumed to mean hours, with minutes assumed to be zero (H or HH). 3 digits is parsed as HMM, and 4 digits is parsed as HHMM. There is no sub-minute resolution.

```
3-1245.Passed out in the yard
```

This means you were busy passed out in the yard from 3:00 to 12:45.

## The "now" Alias

As a shortcut, in any time field, *the letter 'n' can be used as an alias for 'now'*. It will be replaced with the current time.

```
5:-n
```

At 4:00, this command sets the end-time for task 5 as 4:00.

Similarly, if you want to log a task as you are starting it, you can execute something like this:
```
n-Typing WTFDMDG documentation
```

This shortcut create some potential traps, so use caution if you choose to omit the explicit field terminators;

```
n-now I'm making a mistake
```

While this *appears* to create an open task, starting now, entitled "now I'm making a mistake", it *actually* creates a closed task, starting and ending now, entitled "ow I'm making a mistake". Ow, indeed.

```
n-.now I'm not making a mistake
```

```
n-Now, I'm also not making a mistake
```

Because only a lower case "n" is recognized as the "now" shortcut, you can avoid this behavior by always starting your task bodies with upper case letters. Or you can always use the explicit delimiter, or you can just take care to use the delimiter when tasks start with a lower case "n". The choice is yours.

## TODO Tasks

If you want to *plan a task* to be done later (analogous to a sticky-note on your monitor), you can create a task with just a body.

```
Call sam about the paper project
```

Any tasks without start or end times are considered 'todo' items. They are kept at the top of the task list, and emphasized. When you're ready to start one, just use the generated reference number. Assuming that's, for example, 7:

```
7:n-
```

This applies the current time as the start time for task 7.


## Interactive Task Editing

There's also an easier way to edit task bodies (or any other field) than to redefine the entire thing by reference number. From within the command box, pressing Up on your dpad will select the most recently started task. Pressing Down will select the oldest task. Repeated pressing of either key cycles through tasks in the expected direction.

Whenever a task is selected, *a command representing its value is written into the command box*. You can make any edits you want to this command, and pressing enter will apply those edits (unless, of course, you modified or removed the reference number).

# Tags

Tags are words in task bodies which are preceded by forward slashes (/). Each tag has it's own color (though the color will vary as more tags are defined), and this color is used to correspond the tag to items in the timeline visualizer.

## Creating Tags in Task Bodies

There are multiple tag classes. The class for a tag is defined by the number of forward slashes preceding the word.

```
n-On a //call with /Stacy
```

This command creates a task whose body has two tags. The first tag is "call", which is in tag class 2, and "stacy", which is in tag class 1.

The purpose of tag classes is to support visualizing time usage in different ways. For example, I typically use tag class 1 for activities (emailing, meetings, coding, etc), 2 for people, and 3 for projects. When tag class 2 is selected, colors in the timeline visualization will depend strictly on task tags in tag class 2. All other tags will be ignored.

This lets you reflect on which projects you're spending time on, which types of activities you're spending time on, etc.

## Applying Tag-Based Coloring

Selecting tag classes is similar to selecting tasks. However, instead of using Up and Down on your dpad, you'll need to use Shift+Up and Shift+Down.

The current tag class will be the only one with colorized tags in the tag table.

# Timeline Visualizer

This is a simple agenda-style timeline. Each closed task is represented as a block, whose color depends on the task's tags.

* If a task has no tags *in the currently selected tag class*, it remains gray.
* If a task has a single tag in the current class, it is filled with that tag's color.
* If a task has multiple tags in the current class, it is filled with a gradient of those colors.
