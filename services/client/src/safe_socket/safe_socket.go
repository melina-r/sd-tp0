package safe_socket

import "io"

//TODO: Complete with a short-read/short-write tolerant implementation

func SendAll(socket io.Writer, bytes []byte) error {
	bytes_sent, err := socket.Write(bytes)

	for (bytes_sent < len(bytes) && err == nil) {
		bytes_sent, err = socket.Write(bytes[bytes_sent:])
		
	}

	if err != nil {
		return err
	}	

	return nil
}

func RecvAll(socket io.Reader, size int) ([]byte, error) {
	buff := make([]byte, size)
	bytes_read, err := socket.Read(buff)

	for (bytes_read < size && err == nil) {
		bytes_read, err = socket.Read(buff[bytes_read:])
	}

	if err != nil {
		return nil, err
	}
	return buff, nil
}
