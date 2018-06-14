import React from 'react';
import Dropzone from 'react-dropzone';

import Hero from '../components/Hero.jsx';
import DropzoneContent from '../components/DropzoneContent.jsx';

import * as api from '../api.jsx'

const ScanStatus = (props) => {
    let iconClass = 'fa fa-'
    switch (props.scan.status) {
        case 'processing':
            iconClass += 'refresh fa-spin'
            break
        case 'success':
            iconClass += 'check'
            break
        case 'error':
            iconClass += 'times'
            break
    }
    return (
        <div>
            {props.scan.name}&emsp;<i className={iconClass} />
        <i>&nbsp;{props.scan.message}</i>
        </div>
    )
}

class Submissions extends React.Component {

    state = {
        scans: [],
        submissions : [],
        examID: null,
    };

    updateScans = () => {
        api.get('scans/' + this.props.exam.id)
            .then(scans => {
                if (JSON.stringify(scans) != JSON.stringify(this.state.scans)) {
                    this.setState({
                        scans: scans
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
            alert('Please upload a scan PDF.')
            return
        }
        accepted.map(file => {
            const data = new FormData()
            data.append('pdf', file)
            api.post('scans/' + this.props.exam.id, data)
                .then(() => {
                    this.updateScans();
                })
                .catch(resp => {
                    alert('failed to upload pdf (see javascript console for details)')
                    console.error('failed to upload PDF:', resp)
                })
        })
    }

    componentDidMount = () => {
        this.scanUpdater = setInterval(this.updateScans, 1000)
    }

    componentWillUnmount = () => {
        clearInterval(this.scanUpdater);
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
                            <br />
                            <aside className='menu'>
                                <p className='menu-label'>
                                    Previously uploaded
                                </p>
                                <ul className='menu-list'>
                                    {this.state.scans.map(scan =>
                                        <li key={scan.id}>
                                            <ScanStatus scan={scan} />
                                        </li>
                                    )}
                                </ul>
                            </aside>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    }
}

export default Submissions;
