from itertools import starmap
import os
import datetime

import traitlets
from pony import orm

import db


def submission_to_key(sub):
    stud = None if sub.student is None else sub.student.id
    return (stud, sub.id)


class AppModel(traitlets.HasTraits):
    # Immutable
    students = traitlets.List(traitlets.Unicode(), read_only=True)
    graders = traitlets.List(read_only=True)
    exams = traitlets.List(read_only=True)

    exam_id = traitlets.Integer()
    problems = traitlets.List()

    submission_id = traitlets.Integer()
    student = traitlets.Unicode()

    # Stack storing which submissions we have seen, used for working
    # the "prev" button.
    seen_submissions = []

    # Default grader_id = 0 is definitely not in the database.
    # Here we are abusing 1-based indexing and the internal db structure.
    grader_id = traitlets.Integer()

    problem_id = traitlets.Integer()
    n_solutions = traitlets.Integer()
    n_graded = traitlets.Integer()
    feedback_options = traitlets.List()

    selected_feedback = traitlets.List(trait=traitlets.Integer())
    remarks = traitlets.Unicode()

    show_full_page = traitlets.Bool(default_value=False)

    edited_feedback_option = traitlets.Integer()
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
            graders = [(f'{g.first_name} {g.last_name}', g.id)
                       for g in orm.select(g for g in db.Grader)
                                   .order_by(lambda g: g.id)]
        return [("None", 0)] + graders

    ## problems
    @traitlets.default('problems')
    def _default_problems(self):
        with orm.db_session:
            problems = (orm.select(p for p in db.Problem
                                   if p.exam.id == self.exam_id)
                           .order_by(lambda p: p.id))
            return list((p.name, p.id) for p in problems)

    ## exams
    @traitlets.default('exams')
    def _default_exams(self):
        with orm.db_session:
            exams = orm.select(e for e in db.Exam).order_by(lambda e: e.id)
            return [(e.name, e.id) for e in exams]

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
            return (orm.select(p.id for p in db.Problem
                               if p.exam == db.Exam[self.exam_id])
                    .order_by(lambda x:x).first())

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
            return orm.count(s for s in db.Problem[self.problem_id].solutions)

    ## n_graded
    @traitlets.default('n_graded')
    def _default_n_graded(self):
        with orm.db_session:
            return orm.count(s for s in db.Problem[self.problem_id].solutions
                             if s.graded_at is not None)

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
        def formatted(fo):
            text = fo.text + f' ({fo.score})' * (fo.score is not None)
            return text, fo.id

        with orm.db_session:
            fo = (db.Problem[self.problem_id]
                    .feedback_options
                    .order_by(lambda f: f.id))
            return list(formatted(f) for f in fo)

    ## selected_feedback
    @traitlets.default('selected_feedback')
    def _default_selected_feedback(self):
        with orm.db_session:
            sol = db.Solution.get(submission=self.submission_id,
                                  problem=self.problem_id)
            if sol is None:
                return []
            return [f.id for f in sol.feedback]

    ## remarks
    @traitlets.default('remarks')
    def _default_remarks(self):
        with orm.db_session:
            sol = db.Solution.get(submission=self.submission_id,
                                  problem=self.problem_id)
            if sol is None:
                return ''
            return sol.remarks or ''

    ## student
    @traitlets.default('student')
    def _default_student(self):
        with orm.db_session:
            student = db.Submission[self.submission_id].student
            if student is None:
                return "MISSING"
            else:
                return f"{student.id} ({student.first_name} {student.last_name})"

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
        if self.edited_feedback_option:
            with orm.db_session:
                fo = db.FeedbackOption[self.edited_feedback_option]
                assert fo.problem.id == self.problem_id
                self.edited_feedback_name = fo.text or ''
                self.edited_description = fo.description or ''
                self.edited_score = fo.score or 0
        else:
            self.edited_feedback_name = ''
            self.edited_score = 0
            self.edited_description = ''

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
            old_feedback = set(fb.id for fb in solution.feedback)
            old_remarks = solution.remarks
            # Check if anything changed -- if not don't save anything
            if (set(self.selected_feedback) == old_feedback
                    and self.remarks.strip() == old_remarks):
                return

            # Otherwise, save everything
            solution.feedback = [db.FeedbackOption[i] for i
                                 in self.selected_feedback]
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
        with orm.db_session:
            # Check if we create a collision.
            # TODO: reflect a noop in UI via a Valid widget
            if self.edited_feedback_option:
                orig_text = db.FeedbackOption[self.edited_feedback_option].text
            else:
                orig_text = None
            if (self.edited_feedback_name != orig_text
                    and db.FeedbackOption.get(text=self.edited_feedback_name,
                                              problem=self.problem_id)
                        is not None):
                self.edited_feedback_option = 0
                return
        description = self.edited_description.strip()
        score = self.edited_score

        if not self.edited_feedback_option:
            with orm.db_session:
                fo = db.FeedbackOption(text=self.edited_feedback_name,
                                       problem=db.Problem[self.problem_id])
            option = fo.id
        else:
            option = self.edited_feedback_option

        # Set the details in the database.
        with orm.db_session:
            fo = db.FeedbackOption[option]
            fo.text = self.edited_feedback_name.strip()
            fo.description = description
            fo.score = score

        self.feedback_options = []  # hack to fix bug in ipywidgets
        self.feedback_options = self._default_feedback_options()
        self.selected_feedback = self._default_selected_feedback()
        self.edited_feedback_option = option

    def delete_feedback_option(self, *_):
        value = self.edited_feedback_option
        if not value:
            return

        with orm.db_session:
            db.FeedbackOption[value].delete()
            # Some solutions may become ungraded.
            # We should reflect that in the UI
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
            own_sub = db.Submission[self.submission_id]
            own_key = (own_sub, own_sub.student)
            # Note the "wrong" ordering in the second filter.
            # It appears, there's a bug in pony that translates tuple
            # comparison incorrectly
            subs = (db.Submission.select()
                      .filter(lambda s: s.exam.id == self.exam_id)
                      .filter(lambda s: (s, s.student) > own_key)
                      .order_by(lambda s: (s.student, s)))
            result = subs.first()
            if result is None:
                subs = (db.Submission.select()
                          .filter(lambda s: s.exam.id == self.exam_id)
                          .order_by(lambda s: (s.student, s)))
                result = subs.first()

            self.seen_submissions.append(self.submission_id)
            self.submission_id = result.id

    def previous_submission(self):
        try:
            self.submission_id = self.seen_submissions.pop()
        except IndexError:
            pass  # don't move if we have not seen any submissions yet

    def next_ungraded(self):
        with orm.db_session:
            all_ungraded = orm.select(s.submission.id for s in db.Solution
                                      if s.submission.exam.id == self.exam_id
                                      and s.problem.id == self.problem_id
                                      and s.graded_at is None).order_by(lambda
                                                                        x: x)[:]

            for filt in (lambda s: s > self.submission_id, lambda s: True):
                try:
                    next_sub_id = next(filter(filt, all_ungraded))
                    self.seen_submissions.append(self.submission_id)
                    self.submission_id = next_sub_id
                    return
                except StopIteration:
                    continue

    def jump_to_student(self, nr):
        with orm.db_session:
            sub = db.Submission.select(lambda s: s.exam.id==self.exam_id
                                               and s.student.id==nr).first()
            sub_id = sub.id if sub else None
        if sub_id is None:
            return

        self.seen_submissions.append(self.submission_id)
        self.submission_id = sub_id

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
                # the '.' at the end is important, otherwise this would
                # match 'page12' when we were meant to be looking for 'page1'
                page = f'page{int(problem_metadata.page)}.'
                # Here we use the specific page naming scheme because the
                # database does not store the page order.
                # Eventually the database should be restructured to make
                # this easier.
                page_image_path = (s.submission.pages
                                    .select(lambda p: page in p.path)
                                    .first().path)
                if self.show_full_page:
                    with open(page_image_path, 'rb') as f:
                        image = f.read()
                elif s.image_path != 'None':
                    with open(s.image_path, 'rb') as f:
                        image = f.read()
                else:
                    image = db.get_widget_image(page_image_path,
                                                problem_metadata)

                graded_at = s.graded_at

                if s.graded_by:
                    grader_name =  (f'{s.graded_by.first_name} '
                                    f'{s.graded_by.last_name}')
            return image, (grader_name, graded_at)

    def exam_metadata(self):
        with orm.db_session:
            fname = db.Exam[self.exam_id].yaml_path
        return db.read_yaml(fname)
