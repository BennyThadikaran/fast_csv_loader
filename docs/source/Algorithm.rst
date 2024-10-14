Algorithm
=========

This is a broad overview of the ``csv_loader`` algorithm. To get more detailed understanding, please read the actual code.

To maximise efficiency, all operations are performed in binary.

Assume you wish to load the last 160 lines of the file. 
     
1. Get the file size.
2. If the size if less than ``chunk_size`` (or 19 kb whichever is higher),

   - If ``end_date`` is provided:

     - Filter the data upto the ``end_date`` and return the last 160 lines

   - Load the entire file and return the last 160 lines.

3. Read the first line of file to get the column header.

4. Seek to the end of the file.

5. Read the last N bytes (Chunk) of the file.

6. On the first chunk, get a count of line breaks (``\n``) in the chunk to estimate lines per chunk.

7. On every chunk,

   - Update the number of lines read by adding the lines per chunk.

   - Store the chunks in a list

   - If ``end_date`` is specified, we parse the first date string in the chunk to check if we're past the ``end_date``

     - If yes, we continue, until desired number of lines have been loaded.

8. Once we have the desired number of lines,

   - Append the column header and final chunk.
   - Reverse the list and join it into a io.BytesIO object.

9. Load it into a Pandas DataFrame and return the slice of data required.

