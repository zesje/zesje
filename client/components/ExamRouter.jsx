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
    this.props.selectExam(this.props.examID)
  }

  componentDidUpdate = (prevProps, prevState) => {
    if (prevProps.examID !== this.props.examID) {
      this.props.selectExam(this.props.examID)
    }
  }

  deleteExam = (history, examID) => {
    return api
      .del('exams/' + examID)
      .then(() => {
        this.updateExamList()
        history.push('/')
      })
  }

  render = () => {
    const parentURL = this.props.parentURL
    return (
      <Switch>
        <Route path={`${parentURL}/scans`} render={({ match }) =>
          <Scans examID={this.props.examID} />}
        />
        <Route path={`${parentURL}/students`} render={({ match }) =>
          <Students examID={this.props.examID} />}
        />
        <Route path={`${parentURL}/grade/:submissionID?/:problemID?`} render={({ match, history }) => (
          this.props.graderID ? (
            <Grade
              examID={this.props.examID}
              graderID={this.props.graderID}
              history={history}
              parentURL={parentURL}
              submissionID={match.params.submissionID}
              problemID={match.params.problemID} />
          ) : <Fail message='No grader selected. Please do not bookmark URLs' />
        )} />
        <Route path={`${parentURL}/overview`} render={({ match }) => (
          <Overview examID={this.props.examID} />
        )} />
        <Route path={`${parentURL}/email`} render={({ match }) => (
          <Email examID={this.props.examID} />
        )} />
        <Route path={`${parentURL}`} render={({ match, history }) =>
          <Exam
            examID={this.props.examID}
            updateExamList={this.props.updateExamList}
            deleteExam={(id) => this.deleteExam(history, id)}
            setHelpPage={this.props.setHelpPage} />} />
      </Switch>
    )
  }
}

export default ExamRouter
