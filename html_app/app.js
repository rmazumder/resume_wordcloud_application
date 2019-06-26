


var app = angular.module("resumeWordCloud", []);
app.filter("toArray", function() {
    return function(obj) {
        var result = [];
        angular.forEach(obj, function(val, key) {
            val.KeyID = key
            result.push(val);
        });
        return result;
    };
});
app.filter("filtertextRegex", function() {
    return function(input, regex) {
        var patt = new RegExp(regex, 'i');
        var out = [];
        for (var i = 0; i < input.length; i++) {
            if (patt.test(input[i].textData)) {
                out.push(input[i]);
            }
        }
        return out;
    };
});
app.controller("myCtrl", function($scope, $http, $timeout, $filter) {
    $scope.albumBucketName = 'testwc-ruhul';
    var bucketRegion = 'us-east-1';
    var IdentityPoolId = 'us-east-1:1e80c2ea-956a-4a59-a755-cd4aec0ee118';
    $scope.showAlert = true;
    $scope.alertMessage = {
        message: 'Welcome to word cloud resume application'
    }
    AWS.config.update({
        region: bucketRegion,
        credentials: new AWS.CognitoIdentityCredentials({
            IdentityPoolId: IdentityPoolId
        })
    });

    $scope.dispData = {};
    $scope.imageData = {};
    $scope.textData = {};
    $scope.dispArray = [];



    //$scope.resume = ["sdss","sds"]
    var s3 = new AWS.S3({
        apiVersion: '2006-03-01',
        params: {
            Bucket: $scope.albumBucketName
        }
    });


    function listResumeBucket() {
        $scope.alertMessage = {
            message: 'Loading Resumes from Server ....'
        }

        var params = {
            Prefix: 'resume',
            //MaxKeys: 2
        };
        s3.listObjects(params, function(err, data) {
            if (err) console.log(err, err.stack); // an error occurred
            else {

                for (i = 0; i < data.Contents.length; i++) {
                    key = data.Contents[i]["Key"]
                    if (key === "resume/")
                        continue;
                    key = key.substring(7);
                    $scope.dispData[key] = data.Contents[i];
                }
                //$scope.dispArray = $filter('toArray')($scope.dispData);
                //console.log($scope.dispArray)
                $scope.$apply(); // successful response
                dynamo();
            }
        })
    }

    function listImageBucket() {
        var params = {
            Prefix: 'image',
            //MaxKeys: 2
        };
        s3.listObjects(params, function(err, data) {
            if (err) console.log(err, err.stack); // an error occurred
            else {
                var href = this.request.httpRequest.endpoint.href;
                $scope.bucketUrl = href + $scope.albumBucketName + '/';
                for (i = 0; i < data.Contents.length; i++) {
                    key = data.Contents[i]["Key"]
                    if (key === "image/")
                        continue;

                    key = key.substring(6, key.lastIndexOf('.'))
                    $scope.imageData[key] = data.Contents[i];

                }
                $scope.alertMessage = {
                    message: 'Data Refreshed'
                }
                $scope.$apply(); // successful response
                $timeout($scope.hideAlert, 3000);
            }
        })
    }

    $scope.hideAlert = function() {
        $scope.alertMessage = {
            message: 'Welcome to WordCloud Resume Application. Please choose a file and upload Resume. Current supported formats are pdf, doc, docx and image file'
        }
    }

    listResumeBucket();
    listImageBucket();

    $scope.uploadFile = function() {

        var file = document.getElementById('myresume').files[0]
        $scope.alertMessage = {
            message: 'Uploading new file to server: ' + file.name + ' ......'
        }

        var fileName = file.name;
        var albumPhotosKey = encodeURIComponent("resume") + '/';
        var photoKey = albumPhotosKey + fileName;
        s3.upload({
            Key: photoKey,
            Body: file,
            ACL: 'public-read'
        }, function(err, data) {
            if (err) {
                $scope.alertMessage = {
                    message: 'Error uploading the file'
                }
                $timeout($scope.hideAlert, 3000);

            }
            $scope.alertMessage = {
                message: 'File uploaded Successfully'
            }
            listResumeBucket();
            listImageBucket();

        });

    };

    function dynamo() {
        var ddb = new AWS.DynamoDB({
            apiVersion: '2012-08-10'
        });

        var params = {
            ExpressionAttributeValues: {
                ':topic': {
                    S: 'resume'
                }
            },
            ProjectionExpression: 'resumekey, resumetext, imagekey, email, phone',
            FilterExpression: 'begins_with (resumekey, :topic)',
            TableName: 'resumewordcloudTable'
        };

        ddb.scan(params, function(err, data) {
            if (err) {
                console.log("Error", err);
            } else {
                data.Items.forEach(function(element, index, array) {
                    key = element.resumekey.S.substring(7);
                    $scope.textData[key] = element.resumetext.M;
                    textString = "";
                    angular.forEach(element.resumetext.M, function(value, key) {
                        textString = textString + " " + key;
                    });
                    if($scope.dispData[key]){
                      $scope.dispData[key]['textData'] = textString;
                      $scope.dispData[key]['email'] = element.email.S;
                      $scope.dispData[key]['phone'] = element.phone.S;
                    }
                });
                $scope.$apply();

            }
        })
    };


});
