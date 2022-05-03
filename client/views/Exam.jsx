import React from 'react'

import Loading from './Loading.jsx'
import Fail from './Fail.jsx'
import ConfirmationModal from '../components/ConfirmationModal.jsx'
import ExamTemplated from './exam/ExamTemplated.jsx'
import ExamUnstructured from './exam/ExamUnstructured.jsx'

import * as api from '../api.jsx'

class Exam extends React.Component {
  state = {
    exam: undefined,
    deletingExam: false,
    status: ''
  }

  componentDidUpdate = (prevProps, prevState) => {
    if (prevProps.examID !== this.props.examID) {
      this.loadExam(this.props.examID)
    }
  }

  componentDidMount = () => {
    this.loadExam(this.props.examID)
  }

  loadExam = () => {
    if (!this.props.examID) return

    return api.get(`exams/${this.props.examID}`)
      .then(resp => {
        this.setState({ exam: resp })
      })
      .catch(err => {
        console.log(err)
        err.json().then(data => {
          this.setState({ exam: null, status: data.message })
        })
      })
  }

  renderExamContent = () => {
    const layout = this.state.exam.layout
    const commonProps = {
      exam: this.state.exam,
      examID: this.state.exam.id,
      examName: this.state.exam.name,
      updateExamList: this.props.updateExamList,
      updateExam: this.loadExam,
      deleteExam: () => { this.setState({ deletingExam: true }) }
    }

    if (layout === 'templated') {
      // templated exam
      return (
        <ExamTemplated
          setHelpPage={this.props.setHelpPage}
          {...commonProps}
        />
      )
    } else if (layout === 'unstructured') {
      // unstructured
      return (
        <ExamUnstructured
          {...commonProps}
        />
      )
    }
  }

  render () {
    const exam = this.state.exam

    if (exam === undefined) return <Loading />

    if (!exam && this.state.status) {
      return <Fail message={this.state.status} />
    }

    return (
      <>
        {exam
          ? <>{this.renderExamContent()}</>
          : <p className='is-size-5'>{this.state.status}</p>}

        {exam && <ConfirmationModal
          active={this.state.deletingExam}
          color='is-danger'
          headerText={`Are you sure you want to delete exam "${exam.name}"?`}
          confirmText='Delete exam'
          onCancel={() => this.setState({ deletingExam: false })}
          onConfirm={() => {
            this.props.deleteExam(exam.id)
          }} />}
      </>
    )
  }
}

export default Exam
