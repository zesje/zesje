// Javascript does not have built-in functionality to do proper typechecking
// https://stackoverflow.com/questions/7893776/the-most-accurate-way-to-check-js-objects-type

function _typeof (a) {
  return Object.prototype.toString.call(a).slice(8, -1)
}

function _fetch (method) {
  return (endpoint, data) => {
    const headers = new window.Headers()
    if (_typeof(data) === 'Object') {
      headers.append('Content-Type', 'application/json')
      data = JSON.stringify(data)
    }

    return window.fetch('/api/' + endpoint, {
      method: method,
      credentials: 'same-origin',
      body: data,
      headers: headers
    })
      .catch(error => console.error('Error: ', error, ' in', method, endpoint, 'with data', data))
      .then(resp => {
        if (!resp.json) throw resp

        resp.json().then(json => {
          if (resp.ok) {
            return json
          } else {
            console.error(json)
            return Promise.reject(json)
          }
        })
      })
  }
}

const get = _fetch('GET')
const post = _fetch('POST')
const put = _fetch('PUT')
const patch = _fetch('PATCH')
const del = _fetch('DELETE')

export { get, post, put, patch, del }
