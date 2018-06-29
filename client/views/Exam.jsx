import React from 'react'

import Hero from '../components/Hero.jsx'
import './Exam.css'
import GeneratedExamPreview from '../components/GeneratedExamPreview.jsx'
import PanelGenerate from '../components/PanelGenerate.jsx'
import ExamEditor from './ExamEditor.jsx'
import update from 'immutability-helper'
import ReactMarkdown from 'react-markdown';
import ExamFinalizeMarkdown from './ExamFinalize.md'

import * as api from '../api.jsx'

class Exams extends React.Component {

    state = {
        examID: null,
        page: 0,
        numPages: null,
        selectedWidgetId: null,
        widgets: {},
        previewing: false,
    }

    static getDerivedStateFromProps = (newProps, prevState) => {
        if (newProps.exam.id != prevState.examID) {
            // initialize array to size of pdf
            const widgets = []
            newProps.exam.problems.forEach(problem => {
                // keep page and name of problem as widget.problem object
                widgets[problem.widget.id] = {
                    ...problem.widget,
                    problem: {
                        id: problem.id,
                        page: problem.page,
                        name: problem.name,
                    }
                }
            })

            newProps.exam.widgets.forEach(examWidget => {
                widgets[examWidget.id] = examWidget
            })

            return {
                examID: newProps.exam.id,
                widgets: widgets,
            }
        }

        return null
    }

    componentDidUpdate = (prevProps) => {
        if (prevProps.examID !== this.props.examID) {
            this.props.updateExam(this.props.examID)
        }
    }

    componentDidMount = () => {
        if (this.props.examID !== this.props.exam.id) this.props.updateExam(this.props.examID)
    }

    deleteWidget = (widgetId, prompt = true) => {
        const widget = this.state.widgets[widgetId]
        if (widget) {
            if (prompt && confirm('Are you sure you want to delete this widget?')) {
                api.del('problems/' + widget.problem.id)
                    .then(() => {
                        this.setState((prevState) => {
                            return {
                                selectedWidgetId: null,
                                widgets: update(prevState.widgets, {
                                    $splice: [[widgetId, 1]],
                                })
                            }
                        })
                    })
                    .catch(err => {
                        console.log(err)
                        // update to try and get a consistent state
                        this.updateExam()
                    })
            }
        }
    }

    updateWidget = (widgetId, newData) => {
        this.setState(prevState => ({
            widgets: update(prevState.widgets, {
                [widgetId]: newData
            })
        }))
    }

    renderContent = () => {
        if (this.state.previewing) {
            return (
                <GeneratedExamPreview
                    examID={this.state.examID}
                    page={this.state.page}
                    onPDFLoad={this.onPDFLoad}
                />
            )
        } else {
            return (
                <ExamEditor
                    finalized={this.props.exam.finalized}
                    widgets={this.state.widgets}
                    examID={this.state.examID}
                    page={this.state.page}
                    numPages={this.state.numPages}
                    onPDFLoad={this.onPDFLoad}
                    updateWidget={this.updateWidget}
                    selectedWidgetId={this.state.selectedWidgetId}
                    selectWidget={(widgetId) => {
                        this.setState({
                            selectedWidgetId: widgetId,
                        })
                    }}
                    createNewWidget={(widgetData) => {
                        this.setState((prevState) => {
                            return {
                                selectedWidgetId: prevState.widgets.length,
                                widgets: update(prevState.widgets, {
                                    $push: [widgetData]
                                })
                            }
                        })
                        this.setState((prevState) => {
                            return {
                                selectedWidgetId: widgetData.id,
                                widgets: update(prevState.widgets, {
                                    [widgetData.id]: {
                                        $set: widgetData
                                    }
                                })
                            }
                        })
                    }}
                />
            )
        }
    }

    Pager = (props) => {
        const isDisabled = props.numPages == null
        const pageNum = isDisabled ? '_' : props.page + 1
        const numPages = isDisabled ? '_' : props.numPages
        return (
            <div className='field has-addons is-mobile'>
                <div className='control'>
                    <button
                        disabled={isDisabled}
                        type='submit'
                        className='button is-link is-rounded'
                        onClick={() => props.setPage(props.page - 1)}
                    >
                        Previous
                    </button>
                </div>
                <div className='control'>
                    <div className='field-text is-rounded has-text-centered is-link'>
                        {'Page ' + pageNum + ' of ' + numPages}
                    </div>
                </div>
                <div className='control'>
                    <button
                        disabled={isDisabled}
                        type='submit'
                        className='button is-link is-rounded'
                        onClick={() => props.setPage(props.page + 1)}
                    >
                        Next
                    </button>
                </div>
            </div>
        )
    }

    onPDFLoad = (pdf) => {
        this.setState((newProps, prevState) => ({
            numPages: pdf.numPages,
        }), () => {
            this.props.updateExam(this.props.examID)
        })
    }

    setPage = (newPage) => {
        this.setState((prevState) => {
            return {
                // clamp the page
                selectedWidgetId: null,
                page: Math.max(0, Math.min(newPage, prevState.numPages - 1))
            }
        })
    }

    SidePanel = (props) => {
        const selectedWidgetId = this.state.selectedWidgetId
        let selectedWidget = selectedWidgetId && this.state.widgets[selectedWidgetId]
        let problem = selectedWidget && selectedWidget.problem
        let widgetEditDisabled = this.state.previewing || !problem

        return (
            <React.Fragment>
                <this.PanelEdit
                    disabled={widgetEditDisabled}
                    onDeleteClick={() => {
                        this.deleteWidget(selectedWidgetId)
                    }}
                    problem={problem}
                    changeProblemName={newName => {
                        this.setState(prevState => ({
                            widgets: update(prevState.widgets, {
                                [selectedWidgetId]: {
                                    problem: {
                                        name: {
                                            $set: newName
                                        }
                                    }
                                }
                            })
                        }))
                    }}
                    saveProblemName={newName => {
                        api.put('problems/' + problem.id + '/name', {name: newName})
                            .catch(e => alert('Could not save new problem name: ' + e))
                    }}
                />
                <this.PanelExamActions />
            </React.Fragment>
        )
    }

    PanelEdit = (props) => {
        return (
            <nav className='panel'>
                <p className='panel-heading'>
                    Problem details
                </p>
                <div className='panel-block'>
                    <div className='field'>
                        <label className='label'>Name</label>
                        <div className='control'>
                            <input
                                disabled={props.disabled}
                                className='input'
                                placeholder='Problem name'
                                value={props.problem ? props.problem.name : ''}
                                onChange={(e) => {
                                    console.log('onChange')
                                    props.changeProblemName(e.target.value)
                                }}
                                onBlur={(e) => {
                                    console.log('onBlur')
                                    props.saveProblemName(e.target.value)
                                }} />
                        </div>
                    </div>
                </div>
                <div className='panel-block'>
                    <button
                        disabled={props.disabled}
                        className='button is-danger is-fullwidth'
                        onClick={() => props.onDeleteClick()}
                    >
                        Delete
                    </button>
                </div>

            </nav>
        )
    }

    PanelExamActions = () => {
        if (this.props.exam.finalized) {
            return <PanelGenerate examID={this.state.examID} />
        }

        return (
            <nav className='panel'>
                <p className='panel-heading'>
                    Actions
                </p>
                <div className='panel-block'>
                { this.state.previewing ?
                    <this.PanelConfirm
                        onYesClick={() =>
                            api.put(`exams/${this.props.examID}/finalized`, 'true')
                               .then(() => {
                                   this.props.updateExam(this.props.examID)
                                   this.setState({previewing: false})
                               })
                        }
                        onNoClick={() => this.setState({
                             previewing: false,
                        })}
                    />
                  :
                    <this.Finalize
                        onFinalizeClicked={() => this.setState({
                            previewing: true,
                        })}
                    />
                }
                </div>
            </nav>
        )
    }

    Finalize = (props) => {
        return (
            <button
                className='button is-link is-fullwidth'
                onClick={() => props.onFinalizeClicked()}
            >
                Finalize
            </button>
        )
    }

    PanelConfirm = (props) => {
        return (
            <nav className='panel'>
                <div className='content'>
                    <ReactMarkdown source={ExamFinalizeMarkdown} />
                </div>
                <div className='panel-heading'>
                    <label className='label'>Are you sure?</label>
                </div>
                <div className='panel-block'>
                    <div className='field has-addons'>
                        <div className='control'>
                            <button
                                disabled={props.disabled}
                                className='button is-danger'
                                onClick={() => props.onYesClick()}
                            >
                                Yes
                            </button>
                        </div>
                        <div className='control'>
                            <button
                                disabled={props.disabled}
                                className='button is-link'
                                onClick={() => props.onNoClick()}
                            >
                                No
                            </button>
                        </div>
                    </div>
                </div>
            </nav>
        )
    }

    render() {
        return <div>
            <Hero />
            <section className='section'>
                <div className='container'>
                    <div className='columns is-centered' >
                        <div className='column is-one-quarter-widescreen is-one-third-desktop editor-side-panel' >
                            <p className='title is-1'>Exam details</p>
                            <p className='subtitle is-3'>{'Selected: ' + this.props.exam.name}</p>
                            <this.Pager
                                page={this.state.page}
                                numPages={this.state.numPages}
                                setPage={this.setPage}
                            />
                            <this.SidePanel examID={this.state.examID} />
                        </div>
                        <div className='column is-narrow editor-content' >
                            {this.renderContent()}
                        </div>
                    </div>
                </div>
            </section>
        </div>
    }
}

export default Exams
