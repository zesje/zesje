import React from 'react';
import Dropzone from 'react-dropzone';

import Hero from '../components/Hero.jsx';
import DropzoneContent from '../components/DropzoneContent.jsx';

import * as api from '../api.jsx'

const StatusPDF = (props) => {
    let iconClass = "fa fa-";
    switch (props.pdf.status) {
        case "processing":
            iconClass += "refresh fa-spin";
            break;
        case "success":
            iconClass += "check";
            break;
        case "error":
            iconClass += "times";
            break;
    }
    return (
        <div>
            {props.pdf.name}&emsp;<i className={iconClass} />
            <i>&nbsp;{props.pdf.message}</i>
        </div>
    )
}

class Exams extends React.Component {

    state = {
        yaml: "",
        pdfs: [],
        examID: null
    };

    putYaml = () => {
        api.patch('exams/' + this.props.exam.id, { yaml: this.state.yaml })
            .then(() => alert('thank you for the update; it was delicious'))
            .catch(resp => {
                alert('failed to update the YAML (see javascript console)')
                console.error('failed to update YAML', resp)
            })
    }

    updateYaml = (event) => {
        this.setState({
            yaml: event.target.value
        })
    }

    updatePDFs = () => {
        api.get('pdfs/' + this.props.exam.id)
            .then(pdfs => {
                if (JSON.stringify(pdfs) != JSON.stringify(this.state.pdfs)) {
                    this.setState({
                        pdfs: pdfs
                    })
                    this.props.updateSubmission()
                }
            })
    }

    onDropPDF = (accepted, rejected) => {
        if (rejected.length > 0) {
            alert('Please upload a PDF..')
            return
        }
        accepted.map(file => {
            const data = new FormData()
            data.append('pdf', file)
            api.post('pdfs/' + this.props.exam.id, data)
                .then(() => {
                    this.updatePDFs();
                })
                .catch(resp => {
                    alert('failed to upload pdf (see javascript console for details)')
                    console.error('failed to upload PDF:', resp)
                })
        })
    }

    componentDidMount = () => {
        this.pdfUpdater = setInterval(this.updatePDFs, 1000)
        if (this.props.urlID !== this.props.exam.id) this.props.updateExam(this.props.urlID)
        if (this.props.exam.id) this.updatePDFs()
    }

    static getDerivedStateFromProps = (newProps, prevState) => {
        if (newProps.exam.id != prevState.examID) {
            return {
                yaml: newProps.exam.yaml,
                pdfs: [],
                examID: newProps.exam.id
            }
        }
        return null
    }
    componentDidUpdate = (prevProps) => {
        if (prevProps.exam.id != this.props.exam.id) this.updatePDFs()
        if (prevProps.urlID !== this.props.urlID) this.props.updateExam(this.props.urlID)
    }

    componentWillUnmount = () => {
        clearInterval(this.pdfUpdater);
    }

    render() {

        return <div>

            <Hero title="Exam details" subtitle={"Selected: " + this.props.exam.name} />

            <section className="section">

                <div className="container">
                    <div className="columns">


                        <div className="column has-text-centered">
                            <h3 className='title'>Tweak the config</h3>
                            <h5 className='subtitle'>to fix possible misalignments</h5>
                            <textarea className="textarea" rows="10"
                                value={this.state.yaml} onChange={this.updateYaml} />
                            <button className='button is-success'
                                onClick={this.putYaml}>
                                Save
                            </button>
                        </div>


                        <div className="column has-text-centered">
                            <h3 className='title'>And upload PDF's</h3>
                            <h5 className='subtitle'>we will work some magic!</h5>
                            <Dropzone accept={"application/pdf"} style={{}}
                                activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                                onDrop={this.onDropPDF}
                                disablePreview
                                multiple
                            >
                                <DropzoneContent />
                            </Dropzone>

                            <br />
                            <aside className="menu">
                                <p className="menu-label">
                                    Previously uploaded
                                </p>
                                <ul className="menu-list">
                                    {this.state.pdfs.map(pdf =>
                                        <li key={pdf.id}><StatusPDF pdf={pdf} /></li>
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

export default Exams;
