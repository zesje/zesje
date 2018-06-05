import React from 'react';
import Dropzone from 'react-dropzone';

import Hero from '../components/Hero.jsx';
import DropzoneContent from '../components/DropzoneContent.jsx';

import * as api from '../api.jsx'

class Submissions extends React.Component {

    state = {
        pdfs: [],
        submissions : [],
        examID: null,
    };

    updatePDFs = () => {
        api.get('scans/' + this.props.exam.id)
            .then(pdfs => {
                if (JSON.stringify(pdfs) != JSON.stringify(this.state.pdfs)) {
                    this.setState({
                        pdfs: pdfs
                    })
                    this.props.updateSubmission()
                    this.updateSubmissions()
                }
            })
    }

    updateSubmissions = () => {
        api.get('scans/' + this.props.exam.id)
            .then(submissions => {
                this.setState({
                    submissions: submissions.map(sub => sub = {id: sub['id'], missing: sub['missing_pages']})
                })
            })
    }

    onDropPDF = (accepted, rejected) => {
        if (rejected.length > 0) {
            alert('Please upload a PDF.')
            return
        }
        accepted.map(file => {
            const data = new FormData()
            data.append('pdf', file)
            api.post('scans/' + this.props.exam.id, data)
                .then(() => {
                    this.updatePDFs();
                })
                .catch(resp => {
                    alert('failed to upload pdf (see javascript console for details)')
                    console.error('failed to upload PDF:', resp)
                })
        })
    }

    render() {

        return <div>

            <Hero title="Exam details" subtitle={"Selected: " + this.props.exam.name} />

            <section className="section">

                <div className="container">
                    <div className="columns">

                        <div className="column has-text-centered">
                            <h3 className='title'>Upload scans</h3>
                            <h5 className='subtitle'>Scanned pdf files</h5>
                            <Dropzone accept={"application/pdf"} style={{}}
                                activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                                onDrop={this.onDropPDF}
                                disablePreview
                                multiple
                            >
                                <DropzoneContent />
                            </Dropzone>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    }
}

export default Submissions;
