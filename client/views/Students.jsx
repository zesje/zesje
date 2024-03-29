import React from 'react'
import ReactDOMServer from 'react-dom/server'
import { toast } from 'bulma-toast'

import * as api from '../api.jsx'

import Loading from './Loading.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import SearchBox from '../components/SearchBox.jsx'
import Img from '../components/Img.jsx'
import withShortcuts from '../components/ShortcutBinder.jsx'
import withRouter from '../components/RouterBinder.jsx'
import ConfirmationModal from '../components/modals/ConfirmationModal.jsx'
import Fail from './Fail.jsx'

import SearchPanel from './students/SearchPanel.jsx'
import EditPanel from './students/EditPanel.jsx'

import '../components/SubmissionNavigation.css'

const ConfirmMergeModal = (props) => {
  if (!props.student) return null

  let msg = ''
  const other = props.otherCopies

  msg = <p>
    Student #{props.student.id} is already matched with {other.length > 1 ? 'copies' : 'copy'}&nbsp;
    {other.reduce((prev, c, index) =>
      prev + `${c}${index < other.length - 2 ? ', ' : (index === other.length - 1 ? '' : ' and ')}`, '')}.
    &nbsp;This action will merge {other.length > 1 ? 'them' : 'it'}
    &nbsp;with this copy which might affect the total score of the problem.
    &nbsp;Moreover, the solution will have to be approved again.
    <br/>
    Note that this action cannot be undone automatically.
  </p>

  return <ConfirmationModal
    headerText={'Are you sure you want to merge these copies?'}
    contentText={msg}
    color='is-danger'
    confirmText='Merge copies'
    active
    onConfirm={props.onConfirm}
    onCancel={props.onCancel}
  />
}

class CheckStudents extends React.Component {
  searchInput = React.createRef()
  /**
   * Constructor sets empty state, and requests copies for the exam.
   * After getting the copies, if the copyNumber is provided in the URL, loads the corresponding copy,
   * else loads the first copy in the list and then replaces the URL to match the copy.
   */
  constructor (props) {
    super(props)
    this.state = {}
    const partialState = {
      examID: this.props.examID,
      editActive: false,
      editStudent: null,
      confirmStudent: null,
      waitingForValidation: false
    }
    api.get(`copies/${this.props.examID}`).then(copies => {
      const copyNumber = this.props.router.params.copyNumber || copies[0].number
      api.get(`copies/${this.props.examID}/${copyNumber}`).then(copy => {
        this.setState({
          copies,
          copy,
          index: copies.findIndex(c => c.number === copy.number),
          ...partialState
        }, () => this.props.router.navigate(this.getURL(copyNumber), { replace: true }))
      }).catch(_ => {
        this.setState({
          copies,
          copy: null,
          index: 0,
          ...partialState
        })
      })
    }).catch(_ => {
      this.setState({
        copies: [],
        copy: null,
        index: 0,
        ...partialState
      })
    })
  }

  fetchCopyFromUrl = () => {
    const copyNumber = this.props.router.params.copyNumber || this.state.copies[0].number
    api.get(`copies/${this.props.examID}/${copyNumber}`).then(copy => {
      this.setState({
        copy,
        index: this.state.copies.findIndex(c => c.number === copy.number)
      }, () => this.props.router.navigate(this.getURL(copyNumber)), { replace: true })
    }).catch(_ => {
      this.setState({
        copy: null,
        index: 0
      })
    })
  }

  getURL = (copyNumber) => `/exams/${this.props.examID}/students/${copyNumber}`

  componentDidMount = () => {
    // If we change the keybindings here we should also remember to
    // update the tooltips for the associated widgets (in render()).
    // Also add the shortcut to ./client/components/help/ShortcutsHelp.md
    this.props.bindShortcut(['left', 'h'], (event) => {
      event.preventDefault()
      this.prev()
    })
    this.props.bindShortcut(['right', 'l'], (event) => {
      event.preventDefault()
      this.next()
    })
    this.props.bindShortcut(['up', 'k'], (event) => {
      event.preventDefault()
      this.nextUnchecked()
    })
    this.props.bindShortcut(['down', 'j'], (event) => {
      event.preventDefault()
      this.prevUnchecked()
    })
  }

  componentDidUpdate = (prevProps, prevState) => {
    const copyNumber = this.state.copy && String(this.state.copy.number)
    if ((prevProps.examID !== this.props.examID && this.props.examID !== this.state.examID) ||
      (prevProps.router.params.copyNumber !== this.props.router.params.copyNumber &&
        (!copyNumber || this.props.router.params.copyNumber !== copyNumber))) {
      // The URL has changed and at least one of exam id, copy does not match the URL
      // or the URL has changed and copy is not defined
      this.updateFromUrl()
    }
  }

  /**
   * Updates the copies for the current exam.
   * It then calls fetchCopyFromUrl to update the copy in the state according to the URL.
   * In case of unwanted behaviour, sets the copy to null for displaying error component.
   */
  updateFromUrl = () => {
    api.get(`copies/${this.props.examID}`)
      .then(copies =>
        this.setState({
          copies
        }, this.fetchCopyFromUrl)
      ).catch(_ =>
        this.setState({
          copies: [],
          copy: null,
          index: 0
        })
      )
  }

  loadCopy = (index) => {
    if (index >= 0 && index < this.state.copies.length) {
      this.props.router.navigate(this.getURL(this.state.copies[index].number))
      if (this.searchInput.current) {
        this.searchInput.current.clear()
      }
    }
  }

  selectCopy = (copy) => this.loadCopy(this.state.copies.findIndex(c => c.number === copy.number))

  prev = () => this.loadCopy(this.state.index - 1)
  next = () => this.loadCopy(this.state.index + 1)

  prevUnchecked = () => {
    if (!this.state.copies) return

    for (let i = this.state.index - 1; i >= 0; i--) {
      if (this.state.copies[i].validated === false) {
        this.loadCopy(i)
        return true
      }
    }
    return false
  }

  nextUnchecked = () => {
    if (!this.state.copies) return

    for (let i = this.state.index + 1; i < this.state.copies.length; i++) {
      if (this.state.copies[i].validated === false) {
        this.loadCopy(i)
        return true
      }
    }
    return false
  }

  matchStudent = (stud, force = false) => {
    if (!this.state.copies || this.state.waitingForValidation) return

    // Make sure there are no concurrent requests
    this.setState({ waitingForValidation: true })
    api.put(`copies/${this.props.examID}/${this.state.copies[this.state.index].number}`,
      { studentID: stud.id, allowMerge: force })
      .then(resp => {
        this.setState({ confirmStudent: null })

        if (!this.nextUnchecked()) this.updateFromUrl()

        if (force) {
          const msg = <p>Student matched with copy {this.state.copies[this.state.index].number}, go to&nbsp;
          <a href={`/exams/${this.state.examID}/grade/${resp.new_submission_id}`}>Grade</a>&nbsp;
          to approve the merged submission.</p>

          toast({
            message: ReactDOMServer.renderToString(msg),
            type: 'is-success',
            pauseOnHover: true,
            duration: 5000
          })
        }
      })
      .catch(err => {
        if (err.status === 409) {
          this.setState({ confirmStudent: stud, otherCopies: err.other_copies })
        } else {
          toast({ message: `Failed to validate copy: ${err.message}`, type: 'is-danger' })
        }
      })
      .finally(() => this.setState({ waitingForValidation: false }))
  }

  toggleEdit = (student) => {
    if (student && student.id) {
      this.setState({
        editActive: true,
        editStud: student,
        prevSearch: this.searchInput.current.state.input
      })
    } else {
      this.setState({
        editActive: !this.state.editActive,
        editStud: null,

        // save the previous search when the `add students` is pressed from the `SearchPanel`
        prevSearch: !this.state.editActive ? this.searchInput.current.state.input : this.state.prevSearch
      })
    }
  }

  render () {
    const copies = this.state.copies

    if (copies === undefined) {
      // copies are being loaded, we just want to show a loading screen
      return <Loading />
    }

    const copy = this.state.copy
    const validated = copy && copy.validated
    const total = copies.length
    const done = copies.filter(c => c.validated).length
    const hasUnmatchedRight = done === total ? false : copies.some((c, j) => (j > this.state.index) && !c.validated)
    const hasUnmatchedLeft = done === total ? false : copies.some((c, j) => (j < this.state.index) && !c.validated)

    if (!this.state.examID) {
      return <Fail message='No copies where found for this exam' />
    }

    return (
      <>
            <div className='columns'>
              <div className='column is-one-quarter-desktop is-one-third-tablet'>
                {this.state.editActive
                  ? <EditPanel toggleEdit={this.toggleEdit} editStud={this.state.editStud} />
                  : <SearchPanel
                    matchStudent={this.matchStudent} toggleEdit={this.toggleEdit} copy={copy}
                    student={copy && copy.student} validated={validated} copyIndex={this.state.index}
                    ref={this.searchInput} prevSearch={this.state.prevSearch}
                    />}
              </div>

              {this.state.copies.length
                ? <div className='column'>
                  <div className='level'>
                    <div className='level-item make-wider'>
                      <div className='field has-addons is-mobile'>
                        <div className='control'>
                          <button
                            type='submit' className='button is-info is-rounded is-hidden-mobile'
                            onClick={this.prevUnchecked}
                            disabled={!hasUnmatchedLeft}
                          >unchecked
                          </button>
                        </div>
                        <div className='control'>
                          <button
                            type='submit'
                            className={'button is-radiusless' + (validated ? ' is-success' : ' is-link')}
                            onClick={this.prev}
                            disabled={this.state.index === 0}
                          >Previous
                          </button>
                        </div>
                        <div className='control is-wider'>
                          <SearchBox
                            placeholder='Search for a copy'
                            selected={copy}
                            options={copies}
                            suggestionKeys={[
                              'number',
                              'student.firstName',
                              'student.lastName',
                              'student.id'
                            ]}
                            setSelected={this.selectCopy}
                            renderSelected={({ number, student }) => {
                              if (student) {
                                return `Copy #${number}: ${student.firstName} ${student.lastName} (${student.id})`
                              } else {
                                return `Copy #${number}`
                              }
                            }}
                            renderSuggestion={(copy) => {
                              const stud = copy.student
                              if (stud) {
                                return (
                                  <div className='flex-parent'>
                                    <span className='flex-child truncated'>
                                      <b>#{copy.number}</b>
                                      {` ${stud.firstName} ${stud.lastName}`}
                                    </span>
                                    <i className='flex-child fixed'>
                                      ({stud.id})
                                    </i>
                                  </div>
                                )
                              } else {
                                return `#${copy.number}: No student`
                              }
                            }}
                          />
                        </div>
                        <div className='control'>
                          <button
                            type='submit' className={'button is-radiusless' + (validated ? ' is-success' : ' is-link')}
                            onClick={this.next}
                            disabled={this.state.index === total - 1}
                          >Next
                          </button>
                        </div>
                        <div className='control'>
                          <button
                            type='submit' className='button is-info is-rounded is-hidden-mobile'
                            onClick={this.nextUnchecked}
                            disabled={!hasUnmatchedRight}
                          >unchecked
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                  <ProgressBar done={done} total={total} />

                  <div className='box'>
                    <Img
                      src={`api/images/signature/${this.state.examID}/${copy && copy.number}` }
                      alt={copy != null ? `Signature image #${copy.number}` : ''}
                      error={
                        <div className='notification is-danger has-text-centered'>
                          Error loading image, try reloading the page.
                      </div>
                    }
                    />
                  </div>

                </div>
                : null}
            </div>

            <ConfirmMergeModal
              student={this.state.confirmStudent}
              otherCopies={this.state.otherCopies}
              onConfirm={() => this.matchStudent(this.state.confirmStudent, true)}
              onCancel={() => { this.setState({ confirmStudent: null, otherCopies: [] }) }}
            />
      </>
    )
  }
}

export default withRouter(withShortcuts(CheckStudents))
