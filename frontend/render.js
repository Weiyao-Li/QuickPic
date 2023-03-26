document.getElementById('displaytext').style.display = 'none';

function searchPhoto() {
  var apigClient = apigClientFactory.newClient();

  var user_message = document.getElementById('note-textarea').value;

  var body = {};
  var params = { q: user_message };
  var additionalParams = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  apigClient
    .searchGet(params, body, additionalParams)
    .then(function (res) {
      var resp_data = res.data;
      console.log(resp_data)
      if (resp_data.results=="No Results found") {
         document.getElementById('displaytext').innerHTML =
             'Sorry could not find the image. Try another search words!' ;
         document.getElementById('displaytext').style.display = 'block';
       }


      resp_data.results.forEach(function (obj) {
        var img = new Image();
        console.log(obj);
        img.src = obj;
        img.setAttribute('class', 'banner-img');
        img.setAttribute('alt', 'effy');
        document.getElementById('displaytext').innerHTML =
          'Images returned are : ';
        document.getElementById('img-container').appendChild(img);
        document.getElementById('displaytext').style.display = 'block';
      });
    })
    .catch(function (result) {});
}

function getBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    // reader.onload = () => resolve(reader.result)
    reader.onload = () => {
      let encoded = reader.result.replace(/^data:(.*;base64,)?/, '');
      if (encoded.length % 4 > 0) {
        encoded += '='.repeat(4 - (encoded.length % 4));
      }
      resolve(encoded);
    };
    reader.onerror = (error) => reject(error);
  });
}

function uploadPhoto() {
  var fileInput = document.getElementById('file_path');
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  var apigClient = apigClientFactory.newClient();
  var params = {
    "object": fileInput.files[0].name,
    'x-amz-meta-customLabels': note_customtag.value,
  };
  console.log(note_customtag.value)
  var additionalParams = {};
  apigClient
      .uploadObjectPut(params, formData, additionalParams)
      .then(function (res) {
        if (res.status == 200) {
          document.getElementById('uploadText').innerHTML =
              ':) Your image is uploaded successfully!';
          document.getElementById('uploadText').style.display = 'block';
        }
      });
}

