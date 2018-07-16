import React from 'react'

class TabbedPanel extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      selected: 0
    }
  }

  render () {
    return (
      <React.Fragment>
        <div className='panel-tabs'>
          {
            this.props.panels.map((panel, i) => (
              <a
                key={i}
                className={i === this.state.selected ? 'is-active' : ''}
                onClick={() => this.setState({ selected: i })}
              >
                {panel.name}
              </a>
            ))
          }
        </div>
        {
          this.props.panels.map(({ panel }, i) => (
            <div
              className='panel-block'
              key={i}
              style={
                this.state.selected !== i
                  ? { display: 'none' }
                  : null
              }
            >
              {panel}
            </div>
          ))
        }
      </React.Fragment>
    )
  }
}

export default TabbedPanel
