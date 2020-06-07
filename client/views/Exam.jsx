import React from 'react'

import Hero from '../components/Hero.jsx'
import ConfirmationModal from '../components/ConfirmationModal.jsx'
import ExamZesje from './exam/ExamZesje.jsx'
import ExamUnstructured from './exam/ExamUnstructured.jsx'

import * as api from '../api.jsx'

class Exams extends React.Component {
  state = {
    exam: null,
    deletingExam: false,
    status: ''
  }

  componentDidUpdate = (prevProps, prevState) => {
    // in better days we should store and update the exam here and not in App.
    if (prevProps.examID !== this.props.examID) {
      this.loadExam(this.props.examID)
    }
  }

  componentDidMount = () => {
    this.loadExam(this.props.examID)
  }

  loadExam = (id) => {
    if (!id) return

    return api.get(`exams/${id}`)
      .then(resp => {
        this.setState({exam: resp})
      })
      .catch(err => {
        console.log(err)
        err.json().then(data => {
          this.setState({exam: null, status: data.message})
        })
      })
  }

  renderExamContent = () => {
    const layout = this.state.exam.layout.value
    const commonProps = {
      'examID': this.state.exam.id,
      'examName': this.state.exam.name,
      'updateExamList': this.props.updateExamList,
      'updateExam': this.loadExam
    }

    if (layout === 1) {
      // zesje exam
      return <ExamZesje
        exam={this.state.exam}
        deleteExam={() => { this.setState({deletingExam: true}) }}
        setHelpPage={this.props.setHelpPage}
        {...commonProps} />
    } else if (layout === 2) {
      // unstructured
      return <ExamUnstructured
        {...commonProps} />
    }
  }

  render () {
    const exam = this.state.exam

    return <div>
      <Hero />
      <section className='section'>
        <div className='container'>
          {
            exam
              ? (
                <React.Fragment>

                  { this.renderExamContent() }
                </React.Fragment>
              )
              : (
                <p className='issize-5'>{this.state.status}</p>
              )
          }
        </div>
      </section>
      {exam && <ConfirmationModal
        active={this.state.deletingExam}
        color='is-danger'
        headerText={`Are you sure you want to delete exam "${exam.name}"?`}
        confirmText='Delete exam'
        onCancel={() => this.setState({deletingExam: false})}
        onConfirm={() => {
          this.props.deleteExam(exam.id)
        }}
      />}
    </div>
  }
}

export default Exams
