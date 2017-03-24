from itertools import starmap
import os
import datetime

import traitlets
from pony import orm
import yaml

import db
db.use_db('course.sqlite')


class AppModel(traitlets.HasTraits):
    # Immutable
    students = traitlets.List(traitlets.Unicode(), read_only=True)
    graders = traitlets.List(traitlets.Unicode(), read_only=True)
    exams = traitlets.List(traitlets.Unicode(), read_only=True)

    exam_id = traitlets.Integer()
    problems = traitlets.List(traitlets.Unicode())

    submission_id = traitlets.Integer()
    student = traitlets.Unicode()

    # Default grader_id = 0 is definitely not in the database.
    # Here we are abusing 1-based indexing and the internal db structure.
    grader_id = traitlets.Integer()

    problem_id = traitlets.Integer()
    n_solutions = traitlets.Integer()
    n_graded = traitlets.Integer()
    feedback_options = traitlets.List(trait=traitlets.Unicode())

    selected_feedback = traitlets.List(trait=traitlets.Unicode())
    remarks = traitlets.Unicode()

    show_full_page = traitlets.Bool(default_value=False)

    edited_feedback_option = traitlets.Unicode()
    edited_feedback_name = traitlets.Unicode()
    edited_score = traitlets.Integer()
    edited_description = traitlets.Unicode()

    # --- Defaults and validation ---
    ## students
    @traitlets.default('students')
    def _default_students(self):
        with orm.db_session:
            return tuple(starmap('{} ({} {})'.format,
                                 orm.select((s.id, s.first_name, s.last_name)
                                            for s in db.Student)))

    ## graders
    @traitlets.default('graders')
    def _default_graders(self):
        with orm.db_session:
            graders = list(map('{0.first_name} {0.last_name}'.format,
                               orm.select(g for g in db.Grader)
                                  .order_by(lambda g: g.id)))
        return ["None"] + graders

    ## problems
    @traitlets.default('problems')
    def _default_problems(self):
        with orm.db_session:
            problems = (orm.select(p for p in db.Problem
                                   if p.exam.id == self.exam_id)
                           .order_by(lambda p: p.id))
            return list(p.name for p in problems)

    ## exams
    @traitlets.default('exams')
    def _default_exams(self):
        with orm.db_session:
            exams = orm.select(e for e in db.Exam).order_by(lambda e: e.id)
            return list(e.name for e in exams)

    ## exam_id
    @traitlets.default('exam_id')
    def _default_exam_id(self):
        with orm.db_session:
            # Nonempty exam with the most recent yaml
            return sorted(db.Exam.select(lambda e: len(e.submissions)),
                          key=lambda e: os.path.getmtime(e.yaml_path))[-1].id

    @traitlets.validate('exam_id')
    def _valid_exam(self, proposal):
        with orm.db_session():
            if db.Exam.get(id=proposal['value']) is None:
                raise traitlets.TraitError('Unknown exam id.')
        return proposal['value']

    ## submission_id
    @traitlets.default('submission_id')
    def _default_submission_id(self):
        with orm.db_session:
            return (orm.select(s.id for s in db.Submission
                              if s.exam.id == self.exam_id)
                       .order_by(lambda x:x)
                       .first())

    @traitlets.validate('submission_id')
    def _valid_submission_id(self, proposal):
        with orm.db_session():
            sub = db.Submission.get(id=proposal['value'])
            if sub is None:
                raise traitlets.TraitError('Unknown submission id.')
            if sub.exam.id != self.exam_id:
                raise traitlets.TraitError('Submission from a different exam.')
        return proposal['value']

    ## problem_id
    @traitlets.default('problem_id')
    def _default_problem_id(self):
        with orm.db_session:
            return orm.select(p.id for p in db.Problem
                              if p.exam == db.Exam[self.exam_id]).order_by(lambda x:x).first()

    @traitlets.validate('problem_id')
    def _valid_problem_id(self, proposal):
        with orm.db_session():
            prob = db.Problem.get(id=proposal['value'])
            if prob is None:
                raise traitlets.TraitError('Unknown problem id.')
            if prob.exam.id != self.exam_id:
                raise traitlets.TraitError('Problem from a different exam.')
        return proposal['value']

    ## n_solutions
    @traitlets.default('n_solutions')
    def _default_n_solutions(self):
        with orm.db_session:
            return orm.count(s for s in db.Solution if s.problem.id == self.problem_id)

    ## n_graded
    @traitlets.default('n_solutions')
    def _default_n_graded(self):
        with orm.db_session:
            return orm.count(s for s in db.Solution if s.problem.id == self.problem_id
                                                       and s.graded_at is not None)

    ## grader_id
    @traitlets.validate('grader_id')
    def _valid_grader_id(self, proposal):
        new = proposal['value']
        if new == 0:
            return new
        else:
            with orm.db_session:
                if db.Grader.get(id=new) is None:
                    raise traitlets.TraitError('Non-existent grader id.')
        return new

    ## feedback_options
    @traitlets.default('feedback_options')
    def _default_feedback_options(self):
        with orm.db_session:
            return list(orm.select(f.text for f in db.FeedbackOption
                                   if f.problem.id == self.problem_id).order_by('f.id'))

    ## selected_feedback
    @traitlets.default('selected_feedback')
    def _default_selected_feedback(self):
        with orm.db_session:
            sol = db.Solution.get(submission=self.submission_id, problem=self.problem_id)
            if sol is None:
                return []
            return [f.text for f in sol.feedback]

    @traitlets.validate('selected_feedback')
    def _validate_selected_feedback(self, proposal):
        for fb in proposal['value']:
            if fb not in self.feedback_options:
                raise traitlets.TraitError('Selected feedback not in feedback options')
        return proposal['value']

    ## remarks
    @traitlets.default('remarks')
    def _default_remarks(self):
        with orm.db_session:
            sol = db.Solution.get(submission=self.submission_id, problem=self.problem_id)
            if sol is None:
                return ''
            return sol.remarks or ''

    @traitlets.validate('remarks')
    def _validate_remarks(self, proposal):
        return proposal['value'].strip()

    ## student
    @traitlets.default('student')
    def _default_student(self):
        with orm.db_session:
            student = db.Submission[self.submission_id].student
            if student is None:
                return "MISSING"
            else:
                return "{} ({}, {})".format(student.id, student.first_name,
                                            student.last_name)

    # --- Relations between traits ---
    @traitlets.observe('exam_id')
    def _change_exam(self, change):
        self.submission_id = self._default_submission_id()
        self.problems = self._default_problems()
        self.problem_id = self._default_problem_id()

    @traitlets.observe('problem_id', 'submission_id')
    def _change_solution(self, change):
        self.commit_grading(**{change['name']: change['old']})
        self.student = self._default_student()
        self.remarks = self._default_remarks()
        self.feedback_options = []  # hack to fix bug in ipywidgets
        self.feedback_options = self._default_feedback_options()
        self.selected_feedback = self._default_selected_feedback()

    @traitlets.observe('edited_feedback_option')
    def _update_edited_option(self, change):
        if self.edited_feedback_option == 'ADD NEW':
            self.edited_feedback_name = ''
            self.edited_score = 0
            self.edited_description = ''
        else:
            with orm.db_session:
                fo = db.FeedbackOption.get(text=self.edited_feedback_option,
                                           problem=db.Problem[self.problem_id])
                self.edited_description = fo.description or ''
                self.edited_score = fo.score or 0

    # --- Writing into database ---
    def commit_grading(self, submission_id=None, problem_id=None):
        """Commit grading to the database"""
        if submission_id is None:
            submission_id = self.submission_id
        if problem_id is None:
            problem_id = self.problem_id

        # Sometimes we transition from a nonexistent solution and end up here.
        if db.Solution.get(submission=submission_id,
                           problem=problem_id) is None:
            return

        # Should do nothing when the grader is missing.
        if not self.grader_id:
            return

        with orm.db_session:
            solution = db.Solution.get(submission=submission_id,
                                       problem=problem_id)
            old_feedback = set(fb.text for fb in solution.feedback)
            old_remarks = solution.remarks
            # Check if anything changed -- if not don't save anything
            if (set(self.selected_feedback) == old_feedback
                    and self.remarks == old_remarks):
                return

            # Otherwise, save everything
            solution.feedback = orm.select(fb for fb in db.FeedbackOption if
                                           fb.text in self.selected_feedback
                                           and fb.problem.id == problem_id)[:]
            assert len(solution.feedback) == len(self.selected_feedback)
            solution.remarks = self.remarks
            if len(solution.feedback):
                solution.graded_by = db.Grader[self.grader_id]
                solution.graded_at = datetime.datetime.now()
            else:  # if no feedback, then the problem is not graded
                solution.graded_by = None
                solution.graded_at = None

    def commit_feedback_edit(self, *_):
        self.edited_feedback_name = self.edited_feedback_name.strip()
        if not self.edited_feedback_name:
            return
        if self.edited_feedback_name != self.edited_feedback_option:
            # Check if we might create a collision.
            # TODO: reflect a noop in UI via a Valid widget
            with orm.db_session:
                if db.FeedbackOption.get(text=self.edited_feedback_name,
                                         problem=self.problem_id) is not None:
                    self.edited_feedback_option = "ADD NEW"
                    self.edited_feedback_name = ''
                    return
        description = self.edited_description.strip()
        score = self.edited_score

        if self.edited_feedback_option == "ADD NEW":
            with orm.db_session:
                db.FeedbackOption(text=self.edited_feedback_name,
                                  problem=db.Problem[self.problem_id])
            self.feedback_options = []  # hack to fix bug in ipywidgets
            self.feedback_options = self._default_feedback_options()
            self.selected_feedback = self._default_selected_feedback()
            option = self.edited_feedback_name
        else:
            option = self.edited_feedback_option

        # Set the details in the database.
        with orm.db_session:
            fo = db.FeedbackOption.get(text=option,
                                       problem=db.Problem[self.problem_id])
            fo.text = self.edited_feedback_name.strip()
            fo.description = description
            fo.score = score

        new_name = self.edited_feedback_name
        self.feedback_options = []  # hack to fix bug in ipywidgets
        self.feedback_options = self._default_feedback_options()
        self.selected_feedback = self._default_selected_feedback()
        self.edited_feedback_option = new_name

    def delete_feedback_option(self, *_):
        value = self.edited_feedback_option
        if value == "ADD NEW":
            return

        with orm.db_session:
            db.FeedbackOption.get(text=value,
                                  problem=db.Problem[self.problem_id]).delete()
            # Some solutions may become ungraded. We should reflect that in the UI
            for solution in db.Solution.select(lambda s:
                                               s.problem.id == self.problem_id
                                               and not s.feedback):
                solution.graded_by = solution.graded_at = None

        self.feedback_options = []  # hack to fix bug in ipywidgets
        self.feedback_options = self._default_feedback_options()
        self.selected_feedback = self._default_selected_feedback()

    # --- Navigation
    def next_submission(self):
        with orm.db_session:
            subs = orm.select(s.id for s in db.Submission
                              if s.exam.id == self.exam_id
                                 and s.id > self.submission_id)
            result = subs.order_by(lambda x: x).first()
            if result is None:
                self.submission_id = self._default_submission_id()
            else:
                self.submission_id = result

    def previous_submission(self):
        with orm.db_session:
            subs = orm.select(s.id for s in db.Submission
                              if s.exam.id == self.exam_id
                                 and s.id < self.submission_id)

            result = subs.order_by(lambda x: -x).first()
            if result is None:
                subs = orm.select(s.id for s in db.Submission
                                  if s.exam.id == self.exam_id)
                result = subs.order_by(lambda x: -x).first()

            self.submission_id = result

    def next_ungraded(self):
        with orm.db_session:
            all_ungraded = orm.select(s.submission.id for s in db.Solution
                                      if s.submission.exam.id == self.exam_id
                                      and s.problem.id == self.problem_id
                                      and s.graded_at is None).order_by(lambda x: x)[:]

            for filt in (lambda s: s > self.submission_id, lambda s: True):
                try:
                    self.submission_id = next(filter(filt, all_ungraded))
                    return
                except StopIteration:
                    continue

    def jump_to_student(self, nr):
        with orm.db_session:
            sub = db.Submission.get(exam=self.exam_id, student=nr)
            sub_id = sub.id if sub else None
        if sub_id is None:
            return

        self.submission_id = sub_id

    def problem_to_id(self, problem_name):
        with orm.db_session:
            problem = db.Problem.get(exam=self.exam_id, name=problem_name)
            problem_id = problem.id if problem else None
        if problem_id is None:
            problem_id = self.problem_id

        return problem_id

    def problem(self):
        with orm.db_session:
            problem = db.Problem[self.problem_id]
            return problem.name


    def exam_to_id(self, exam_name):
        with orm.db_session:
            exam = db.Exam.get(name=exam_name)
            if not exam:
                raise ValueError('No exam {}'.format(exam_name))
            return exam.id

    def id_to_exam(self, exam_id=None):
        if exam_id is None:
            exam_id = self.exam_id
        with orm.db_session:
            return db.Exam[exam_id].name

    # --- Other methods
    def num_submissions(self, exam_id):
        with orm.db_session:
            return orm.count(s for s in db.Submission if s.exam.id == exam_id)

    def num_graded(self):
        with orm.db_session:
            this_problem = db.Problem[self.problem_id]
            return sum(bool(s.graded_by) for s in this_problem.solutions)

    def get_solution(self):
        with orm.db_session:
            p = db.Problem[self.problem_id]
            s = db.Solution.get(submission=self.submission_id,
                                problem=self.problem_id)

            graded_at = grader_name = None
            image = b''
            if s:
                *_, widgets = self.exam_metadata()
                problem_metadata = widgets.loc[p.name]
                page = int(problem_metadata.page)
                # Here we use the specific page naming scheme because the
                # database does not store the page order.
                # Eventually the database should be restructured to make
                # this easier.
                page_image_path = (s.submission.pages
                                    .select(lambda p: 'page{}'.format(page)
                                            in p.path)
                                    .first().path)
                if self.show_full_page:
                    with open(page_image_path, 'rb') as f:
                        image = f.read()
                elif s.image_path != 'None':
                    with open(s.image_path, 'rb') as f:
                        image = f.read()
                else:
                    image = db.get_widget_image(page_image_path, problem_metadata)

                graded_at = s.graded_at

                if s.graded_by:
                    grader_name =  ('{0.first_name} '
                                    '{0.last_name}').format(s.graded_by)
            return image, (grader_name, graded_at)

    def set_grader(self, name):
        if not name:
            self.grader_id = 0
        else:
            first, *last = name.split()
            last = ' '.join(last)
            with orm.db_session:
                grader = db.Grader.get(first_name=first, last_name=last)
                grader_id = grader.id if grader else 0
            self.grader_id = grader_id

    def exam_metadata(self):
        with orm.db_session:
            fname = db.Exam[self.exam_id].yaml_path
        return db.read_yaml(fname)
