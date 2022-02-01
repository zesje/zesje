import React from 'react'
import { Route, Switch } from 'react-router-dom'
import loadable from '@loadable/component'

import * as api from '../api.jsx'

import Loading from '../views/Loading.jsx'

const Exam = loadable(() => import('../views/Exam.jsx'), { fallback: <Loading /> })
const Scans = loadable(() => import('../views/Scans.jsx'), { fallback: <Loading /> })
const Students = loadable(() => import('../views/Students.jsx'), { fallback: <Loading /> })
const Grade = loadable(() => import('../views/Grade.jsx'), { fallback: <Loading /> })
const Overview = loadable(() => import('../views/Overview.jsx'), { fallback: <Loading /> })
const Email = loadable(() => import('../views/Email.jsx'), { fallback: <Loading /> })
const Fail = loadable(() => import('../views/Fail.jsx'), { fallback: <Loading /> })

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
            <Grade
              examID={parseInt(examID)}
              history={history}
              parentURL={parentURL}
              submissionID={match.params.submissionID ? parseInt(match.params.submissionID) : undefined}
              problemID={match.params.problemID ? parseInt(match.params.problemID) : undefined}
            />
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
