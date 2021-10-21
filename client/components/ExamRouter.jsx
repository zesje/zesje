import React from 'react'
import { Route, Routes, Outlet } from 'react-router-dom'
import loadable from '@loadable/component'
import withRouter from './RouterBinder.jsx'

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
    this.props.selectExam(this.props.router.params.examID)
  }

  componentDidUpdate = (prevProps, prevState) => {
    const { examID } = this.props.router.params
    if (prevProps.router.params.examID !== examID) {
      // sends the selected exam to the navbar
      this.props.selectExam(examID)
    }
  }

  deleteExam = (examID) => {
    return api
      .del('exams/' + examID)
      .then(() => {
        this.props.updateExamList()
        this.props.router.navigate('/', { replace: true })
      })
  }

  render = () => {
    const { examID } = this.props.router.params

    if (!examID || isNaN(examID)) {
      return <Fail message='Invalid exam' />
    }

    return (
      <Routes>
        <Route
          path='scans' element={<Scans examID={examID} />}
        />
        <Route
          path='students' element={<Students examID={examID} />}
        >
          <Route path=':copyNumber' element={<Outlet />} />
        </Route>
        <Route
          path='grade' element={<Grade examID={examID} />}
        >
          <Route path=':submissionID' element={<Outlet />} />
          <Route path=':submissionID/:problemID' element={<Outlet />} />
        </Route>
        <Route
          path='overview' element={<Overview examID={examID} />}
        />
        <Route
          path='email' element={<Email examID={examID} />}
        />
        <Route
          path='/' element={
            <Exam
              examID={examID}
              updateExamList={this.props.updateExamList}
              deleteExam={this.deleteExam}
              setHelpPage={this.props.setHelpPage}
            />}
        />
      </Routes>
    )
  }
}

export default withRouter(ExamRouter)
