import React from 'react'
import { Route, Switch } from 'react-router-dom'

import Exam from '../views/Exam.jsx'
import Scans from '../views/Scans.jsx'
import Students from '../views/Students.jsx'
import Grade from '../views/Grade.jsx'
import Overview from '../views/Overview.jsx'
import Email from '../views/Email.jsx'
import Fail from '../views/Fail.jsx'

import * as api from '../api.jsx'

class ExamContent extends React.Component {
  state = {
    examID: null,
    graderID: null
  }

  componentDidMount = () => {
    this.updateExam(this.props.examID)
  }

  componentDidUpdate = (prevProps, prevState) => {
    const examID = this.props.examID
    if (prevProps.examID !== examID && examID !== this.state.examID) {
      this.updateExam(examID)
    }
  }

  updateExam = (examID) => {
    this.setState({ examID })
    this.props.selectExam(examID)
  }

  deleteExam = (history, examID) => {
    return api
      .del('exams/' + examID)
      .then(() => {
        this.props.updateExamList()
        history.push('/')
      })
  }

  render () {
    return (
      <Switch>
        <Route path='/exams/:examID/scans' render={({ match }) =>
          <Scans examID={this.state.examID} />}
        />
        <Route path='/exams/:examID/students' render={({ match }) =>
          <Students examID={this.state.examID} />}
        />
        <Route path='/exams/:examID/grade/:submissionID?/:problemID?' render={({ match, history }) => (
          this.props.graderID ? (
            <Grade
              examID={this.state.examID}
              graderID={this.props.graderID}
              history={history}
              submissionID={match.params.submissionID}
              problemID={match.params.problemID} />
          ) : <Fail message='No grader selected. Please do not bookmark URLs' />
        )} />
        <Route path='/exams/:examID/overview' render={({ match }) => (
          <Overview examID={this.state.examID} />
        )} />
        <Route path='/exams/:examID/email' render={({ match }) => (
          <Email examID={this.state.examID} />
        )} />
        <Route path='/exams/:examID' render={({ match, history }) =>
          <Exam
            examID={this.state.examID}
            updateExamList={this.updateExamList}
            deleteExam={(id) => this.deleteExam(history, id)}
            setHelpPage={this.props.setHelpPage} />} />
      </Switch>
    )
  }
}

export default ExamContent
