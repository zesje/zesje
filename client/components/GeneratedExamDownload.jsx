import React from 'react'
import ReactMarkdown from 'react-markdown';

import downloadMarkdown from './exam_download.md'

import * as api from '../api.jsx'

class GeneratedExamDownload extends React.Component {

    state = {
        examID: null,
        numberOfCopies: 100,
        isGenerated: false,
        isGenerating: false,
    }

    static getDerivedStateFromProps = (newProps, prevState) => {
        if (newProps.examID != prevState.examID) {
            return {
                examID: newProps.examID
            }
        }
        return null
    }

    onFocus = (e) => {
        e.target.select()
    }

    onChange = (e) => {
        const patt = new RegExp(/^[1-9]\d*$|^()$/);
        if (patt.test(e.target.value)) {
            this.setState({
                numberOfCopies: e.target.value
            })
        }
    }

    onClickGenerate = () => {
        this.setState({
            isGenerating: true,
            isGenerated: false,
        }, () => {
            const data = {
                copies: this.state.numberOfCopies,
            }
            api.post('exams/' + this.state.examID + '/generated_pdfs', data)
                .then(() => {
                    this.setState({
                        isGenerated: true,
                        isGenerating: false,
                    })
                })
        })
    }

    render = () => {

        return (
            <React.Fragment>
                <div className={'columns is-centered'} >
                    <div className='column is-narrow is-one-third content'>
                        <ReactMarkdown source={downloadMarkdown} />
                    </div>
                    <div className='column is-narrow'>
                        <div className='field control has-icons-left'>
                            <input
                                className='input'
                                type='text'
                                maxLength='4'
                                placeholder='Number of copies'
                                value={this.state.numberOfCopies}
                                onChange={this.onChange}
                                onFocus={this.onFocus} />
                            <span className='icon is-small is-left'>
                                <i className='fa fa-copy'></i>
                            </span>
                        </div>
                        <div className='field'>
                            <p className='control'>
                                <a
                                    className={(this.state.isGenerating ? 'is-loading ' : '') + 'is-fullwidth button is-link'}
                                    onClick={this.onClickGenerate}
                                >
                                    Generate
                                </a>
                            </p>
                        </div>
                        <div className='field is-grouped'>
                            <p className='control'>
                                <a
                                    className='button is-primary'
                                    disabled={!this.state.isGenerated}
                                    href={this.state.isGenerated ? '/api/exams/' + this.state.examID + '/generated_pdfs?type=zip' : null}
                                >
                                    Download Zip
                                </a>
                            </p>
                            <p className='control'>
                                <a
                                    className='button is-primary'
                                    disabled={!this.state.isGenerated}
                                    href={this.state.isGenerated ? '/api/exams/' + this.state.examID + '/generated_pdfs?type=pdf' : null}
                                >
                                    Download PDF
                                </a>
                            </p>
                        </div>
                    </div>
                    <div className='column is-narrow is-one-third' />
                </div>
            </React.Fragment>
        )
    }

}

export default GeneratedExamDownload
