import React from 'react'
import { Route, Switch } from 'react-router-dom'
import Loadable from 'react-loadable'

import * as api from '../api.jsx'

import Loading from '../views/Loading.jsx'

const Exam = Loadable({
  loader: () => import('../views/Exam.jsx'),
  loading: Loading
})
const Scans = Loadable({
  loader: () => import('../views/Scans.jsx'),
  loading: Loading
})
const Students = Loadable({
  loader: () => import('../views/Students.jsx'),
  loading: Loading
})
const Grade = Loadable({
  loader: () => import('../views/Grade.jsx'),
  loading: Loading
})
const Overview = Loadable({
  loader: () => import('../views/Overview.jsx'),
  loading: Loading
})
const Email = Loadable({
  loader: () => import('../views/Email.jsx'),
  loading: Loading
})
const Fail = Loadable({
  loader: () => import('../views/Fail.jsx'),
  loading: Loading
})

class ExamRouter extends React.PureComponent {
  componentDidMount = () => {
    this.props.selectExam(this.props.parentMatch.params.examID)
  }

  componentDidUpdate = (prevProps, prevState) => {
    const examID = this.props.parentMatch.params.examID
    if (prevProps.parentMatch.params.examID !== examID) {
      // sends the selected exam to the navbar
      this.props.selectExam(examID)
    }
  }

  deleteExam = (history, examID) => {
    return api
      .del('exams/' + examID)
      .then(() => {
        this.props.updateExamList()
        history.push('/')
      })
  }

  render = () => {
    const examID = this.props.parentMatch.params.examID
    const parentURL = this.props.parentMatch.url

    if (!examID || isNaN(examID)) {
      return <Fail message='Invalid exam' />
    }

    return (
      <Switch>
        <Route
          path={`${parentURL}/scans`} render={({ match }) =>
            <Scans examID={examID} />}
        />
        <Route
          path={`${parentURL}/students`} render={({ match }) =>
            <Students examID={examID} />}
        />
        <Route
          path={`${parentURL}/grade/:submissionID?/:problemID?`} render={({ match, history }) => (
            this.props.graderID
              ? (
              <Grade
                examID={parseInt(examID)}
                graderID={this.props.graderID}
                history={history}
                parentURL={parentURL}
                submissionID={match.params.submissionID ? parseInt(match.params.submissionID) : undefined}
                problemID={match.params.problemID ? parseInt(match.params.problemID) : undefined}
              />
                )
              : <Fail message='No grader selected. Please do not bookmark URLs' />
          )}
        />
        <Route
          path={`${parentURL}/overview`} render={({ match }) => (
            <Overview examID={examID} />
          )}
        />
        <Route
          path={`${parentURL}/email`} render={({ match }) => (
            <Email examID={examID} />
          )}
        />
        <Route
          path={`${parentURL}`} render={({ match, history }) =>
            <Exam
              examID={examID}
              updateExamList={this.props.updateExamList}
              deleteExam={(id) => this.deleteExam(history, id)}
              setHelpPage={this.props.setHelpPage}
            />}
        />
      </Switch>
    )
  }
}

export default ExamRouter
