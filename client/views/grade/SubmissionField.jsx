import React from 'react'
import Autosuggest from 'react-autosuggest'
import Fuse from 'fuse.js'

// When suggestion is clicked, Autosuggest needs to populate the input
// based on the clicked suggestion. Teach Autosuggest how to calculate the
// input value for every given suggestion.
const getSuggestionValue = (submission) => {
  const stud = submission.student
  return stud.firstName + ' ' + stud.lastName + ' (' + stud.id + ')'
}

// Use your imagination to render suggestions.
const renderSuggestion = submission => {
  const stud = submission.student
  return (
    <div>
      <b>{stud.firstName + ' ' + stud.lastName}</b>
      <i> ({stud.id})</i>
    </div>
  )
}

class SubmissionField extends React.Component {
  state = {
    value: '',
    suggestions: []
  }

  onChange = (event, { newValue }) => {
    this.setState({
      value: newValue
    })
  }

  // Autosuggest will call this function every time you need to update suggestions.
  // You already implemented this logic above, so just use it.
  onSuggestionsFetchRequested = ({ value }) => {
    const options = {
      shouldSort: true,
      threshold: 0.6,
      location: 0,
      distance: 100,
      maxPatternLength: 32,
      minMatchCharLength: 1,
      keys: [
        'student.id',
        'student.firstName',
        'student.lastName'
      ]
    }
    const fuse = new Fuse(this.props.submissions, options)
    const result = fuse.search(value) // .slice(0, 10)

    this.setState({
      suggestions: result
    })
  }

  // Autosuggest will call this function every time you need to clear suggestions.
  onSuggestionsClearRequested = () => {
    this.setState({
      suggestions: []
    })
  }

  render () {
    const { value, suggestions } = this.state

    // Autosuggest will pass through all these props to the input.
    const inputProps = {
      className: 'input is-rounded has-text-centered is-link',
      type: 'text',
      placeholder: 'Search for a submission',
      value,
      onChange: this.onChange,
      onSubmit: this.setSubmission
    }

    return (
      <Autosuggest
        suggestions={suggestions}
        onSuggestionsFetchRequested={this.onSuggestionsFetchRequested}
        onSuggestionsClearRequested={this.onSuggestionsClearRequested}
        getSuggestionValue={getSuggestionValue}
        renderSuggestion={renderSuggestion}
        inputProps={inputProps}
      />
    )
  }
}

export default SubmissionField
