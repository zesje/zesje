
# Welcome to zesje

*Zesje* is an online software for grading exams.

As its name suggests, Zesje has been designed as a **minimal working prototype** during our free time so do not expect any degree of polish. Still it can provide a lot of advantages over manual grading, especially when dealing with large courses.

This notebook is a tutorial and a reference documentation for Zesje. If you want to try out different software features, there is a sandbox deployment available at https://sandbox.grading.quantumtinkerer.tudelft.nl; try it out without fear of breaking things. Because of spam concerns, its email sending capabilities are limited to the [`sharklasers.com`](https://sharklasers.com) domain that provides temporary mailboxes accessible by anyone.

## Benefits of using zesje

+ Moving the grading online: you don't need to deal with paper, updating and processing grades is automated. The grading can take place from anywhere.
+ Zesje is faster than paper-based grading, especially for large courses
+ Make grading streamlined by allowing to follow a grading scheme that is both clearly defined and easy to adjust.
+ Export of grades in various formats for postprocessing.
+ Quick built-in analysis for a progress overview.
+ Ability to email students their solutions together with detailed feedback. From the student perspective this is the killer feature.
+ Fully open source: if you want to modify anything and implemennt new functionality, you are welcome to do so.

## Limitations and disclaimer

+ **Zesje is a prototype-level software**: it is tested by people using it. It is not developed by professional web developers, and it certainly has many rough edges.
+ If something breaks, we are very sorry. Most likely we'd be able to fix your problem, but we do not provide any guarantees.
+ Fully trusted users: anyone with the login and password for your zesje installation can do anything.
+ No change history. We do daily backups, but you cannot revert your changes manually.

## Support

If you want to use zesje in a course, we are happy to host it for you, contact us at [zesje@antonakhmerov.org](mailto:zesje@antonakhmerov.org) or [me@josephweston.org](mailto:me@josephweston.org).

We will also sign you up for the zesje support mailing list.

If you have questions about using zesje, please use the following channels:
* if you have a question, use the zesje support chat at https://chat.quantumtinkerer.tudelft.nl/external/channels/zesje (you'll need to create an account and join the **external** team after creating it).
* if you found a bug or if you have a suggestion for improvement, please report it at Zesje [issue tracker](https://gitlab.kwant-project.org/zesje/zesje/issues).

## Initializing a course

Each course will need its own zesje installation, but a single installation can be used to grade multiple exams.

### Adding students

1. Export the student information from Brightspace. To do that go to the course page, select *Grades* → *Enter grades* → *Export grades*. Then choose the options as shown: ![](brightspace_export.png)
2. Browse to [students](/students) and upload the resulting `.csv` file.

You can add more students and edit existing student information at any time. It is currently not possible to remove students from zesje.
You can also add students manually one by one.

### Adding graders

Go to the [graders page](/graders) and add all the names of the graders. Currently zesje considers all the users as trusted, but for the ease of figuring out who graded what, you must tell the app who you are before starting to grade.

## Creating an exam

#### Important warnings:
+ Since every copy of an exam should have a unique copy number, you shouldn't print the same copies twice.
+ Use sufficient space for each answer, and provide an extra answerbox at the end of the exam in case the students run out of space. If that fails, have a student submit **two complete copies of the exam**.

### Create the exam in zesje

1. Upload the pdf of your exam at this [URL (exam selector → Add new)](/exams).
2. Check that the student identification widget and the barcode do not overlap with other text.
3. Mark the places where the students are supposed to write their answers in the preview and add problem names.
4. Finalize the exam (do check that everything looks correct!)
5. Prepare multiple exam copies for printing.

## Scanning and uploading the solutions

### Find a good scanner

There are two types of scanners in TUD: Ricoh Alficio 3001 and Ricoh Alficio 4501. The 4501 model will take several minutes for a large exam, while 3001 lasts more than an hour. Find the 4501 model and use it (there is one in F183 for example).

### Scanner settings

#### Select the "My Home Folder" option:

![Scanner option selection](scan_to_me.jpg)

#### Select the following scanner settings:

![Scanner settings](scan_settings.jpg)

#### Use the paper feed, as shown:

![How to insert exams into the scanner](paper_feed.jpg)

### Uploading the scan results

**Note:** it may take up to an hour after the scanning has physically stopped for the scanners to generate a pdf for large exams.

Once it's done, get it from your webdata by any means, for example at `https://webdata.tudelft.nl/staff-homes/<first letter of last name>/<netid>/My Documents/`

Finally select the correct exam and upload the files via the submissions tab.

**Note:** If you reupload scans of the same pages, these will overwrite the older uploads. Therefore you can always fix problems later if your initial upload isn't good enough.

### Verifying the students

Check that the students are identified correctly in the [students](/students) tab. This is necessary to ensure that all the student numbers are identified correctly.

## Grading an exam

**This section of the documentation is not up to date yet.**

### Video summary:

### Assiging grades and feedback
+ Select the feedback options
+ Add any "specific" feedback for a particular solution, but this is for information purposes only, and does not add/subtract points

### Editing the grading scheme
+ Based on the idea that you can student answers tend to have similarities
+ Zesje allows you to adapt your feedback to student responses while grading
+ You don't need to decide on a final grading scheme beforehand

### Choosing a grading scheme

While you are completely free in choosing the grading scheme, and you should choose the workflow that works best for you, there are several things that you may want to follow.

+ **Important**: Zesje uses integers for all scores. Ensure that the smallest amount of score differences is 1 point.
+ Keep one option with 0 points, and one with the maximal score for the problem.
+ Since the feedback the students see is based on the feedback options you select, for most cases it makes sense to give the students a maximal score and subtract some points for the omissions they made.
+ Choose short and easy to remember names for the feedback options. In the extended description try to outline the part of the solution. The students can see this in an email.

### Modifying a specific student

If you need to navigate to a specific student, use the "jump to student" text field. Thanks to autocompletion, it allows you to search a student by name or their student number.

## Processing results

**UNFINISHED**

Most of the parts should be self-explanatory, however let us list the currently available options:

+ **Problem statistics and scores**:
  Available in the *problem statistics* tab of the [grade](../grade.ipynb) dashboard, it shows a quick-and-dirty summary of the problem grading.
+ **Exam statistics report**:
  Available in the *summary & email* tab of the [grade](../grade.ipynb) dashboard. A rendered html summary with the detailed but anonymized data that shows the score distributions, all the feedback options, scores, and clarifications. Depending on your preferences, it may be shared with the students.
+ **Export grades**
  Available in the *summary & email* tab of the [grade](../grade.ipynb) dashboard.
  - **Spreadsheet (detailed)**: an Excel file with full information about the exam.
  - **Spreadsheet (summary)**: an Excel file containing only scores per problem.
  - **DafaFrame (detailed)**: a [pandas](https://pandas.pydata.org) dataframe with all information, useful for advanced data analysis.
  - **Complete database**: the full internal database, can be used to back up the data and restore (albeit the restoring will require our help).

## Sending feedback

### Prepare an email template
In the *Individual email* tab of the [grade](../grade.ipynb) dashboard you can create an template that will be used to send personalized feedback to the students.

**Warning**: templates are currently not saved, copy them externally if you want to edit them afterwards!

The template is written using the [Jinja 2](http://jinja.pocoo.org/docs/2.9/templates/#template-designer-documentation) templating language. This allows you to intermix regular text with special commands that will do things like optionally include some text if a certain condition is satisfied, or print the contents of some variable (such as the student's name or grade).

Although you can find a comprehensive language reference on the Jinja website, we include some basic usage below.

#### Printing variables
Type a variable name inside double curly braces (`{{`) to have the variable printed in the document, e.g.
```
{{ first_name }}
```
expands to the first name of the student that the template is rendering. Variables can also have *attributes*, which can
be accessed with `.` inside a variable expansion, e.g.
```
your grade is: {{ student.total }}
```
Jinja also includes so-called "filters" that can be used to modify the way a variable is printed. For example,
```
{{ student.first_name | uppercase }}
```
will print the student's first name in uppercase. The Jinja website hasa complete list of available filters.

#### Optionally including text
Include optional text between `{% if <condition> %}` and `{% endif %}` tags, e.g.
```
This text is always included
{% if student.total > 80 %}
Well done {{student.first_name}}; you did very well.
{% endif %}
```

#### Looping
It is possible to loop with the `{% for <item> in <list> %}` `{% endfor %}` tags, e.g.
```
{% for feedback in problem.feedback %}
  your feedback: {{ feedback.short }}
{% endfor %}
```

#### List of variables
Within your templates you can use the **`student`** and **`results`** variables. `student` has several attributes, and `results` is a list (that you can use in a `{% for %}` loop).

##### `student`
+ `first_name`: Student's first name
+ `last_name`: Student's last name
+ `email`: Student's email address
+ `total`: Sum of the `score`s for the student's problems

##### elements of `results`
+ `name`: Problem name
+ `max_score`: Maximum score for the problem
+ `feedback`: List of feedback the student got for this problem. Each
              element has the following attributes:
  - `short`: Short description of the feedback, as used when grading
  - `score`: Score associated with this feedback
  - `description`: Long description of the feedback
+ `score`: Student's score for this problem
+ `remarks`: Student-specific feedback

### Send feedback to indivdual students or everyone

After composing the template you can press the green *Refresh* button to render the template for the current student. It is a good idea to do this for a few students before sending any feedback by email, to make sure that your template is working.

From the same tab (*Individual email*) you can also email the rendered template *for the currently selected student*. It is a good idea to do this for several students and email the results to yourself (by supplying your email in the *Recipients* text box) to ensure that the output is satisfactory. By default the email is not sent to the student.

To send personalized emails to all students, use the *Email results to everyone* button in the *summary & email* tab in the [grade](../grade.ipynb) dashboard. You must first enable this button by checking the *Yes, email everyone* checkbox. Note that sending the emails to everyone may take some time, and it is impossible to interrupt this process. That being said, do not browse away from the *summary & email* tab until the process is completed; the blue progress bar on the top of the screen will disappear.
You will see an error message if some emails were not sent.
