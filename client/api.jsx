// Javascript does not have built-in functionality to do proper typechecking
// https://stackoverflow.com/questions/7893776/the-most-accurate-way-to-check-js-objects-type
function _typeof (a) {
  return Object.prototype.toString.call(a).slice(8, -1)
}

function _fetch (method) {
  return (endpoint, data) => {
    var headers = new Headers()
    if (_typeof(data) == 'Object') {
      headers.append('Content-Type', 'application/json')
      data = JSON.stringify(data)
    }

    return fetch('/api/' + endpoint, {
      method: method,
      credentials: 'same-origin',
      body: data,
      headers: headers
    })
      .catch(error =>
        console.error('Error in', method, endpoint, 'with data', data))
      .then(resp => {
        if (!resp.ok) {
          throw resp
        } else {
          return resp
        }
      })
    // valid responses always return JSON
      .then(r => r.json())
  }
}

const get = _fetch('GET')
const post = _fetch('POST')
const put = _fetch('PUT')
const patch = _fetch('PATCH')
const del = _fetch('DELETE')

export { get, post, put, patch, del }
