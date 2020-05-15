(* Note: GDAL binaries are in:
   /Library/Frameworks/GDAL.framework/Programs *)

open Base
open Stdio

let altitude = 1500.

let interesting = [
  1613;
  1615;
  1623;
  1624;
  1626;
  1627;
]

let convert_to_well_known_text ~input ~output =
  Caml.Sys.remove output;
  let cmd =
    Printf.sprintf "ogr2ogr -f csv -lco GEOMETRY=AS_WKT %s %s" output input
  in
  if Caml.Sys.command cmd <> 0 then failwith "ogr2ogr failed"

let station = ref 0

let parse_coords coords =
  try
    Caml.Scanf.sscanf coords "%f %f" (fun x y ->
      Some (x, y, altitude))
  with _ -> None

let write_survex ~svx_writer ~kat_number ~coords =
  if List.mem interesting kat_number ~equal:Int.equal then begin
    match coords with
    | first::((_::_) as coords) ->
      begin match parse_coords first with
      | None -> ()
      | Some (x, y, z) ->
        let buffer = Buffer.create 1024 in
        let starting_station = !station in
        Printf.bprintf buffer "*fix %d-%d %f %f %f\n"
          kat_number starting_station x y z;
        let rec add_legs ~length ~station ~coords ~prev_x ~prev_y ~prev_z =
          match coords with
          | [] -> Some (length, station + 1)
          | coords::rest ->
            match parse_coords coords with
            | None -> None
            | Some (x, y, z) ->
              let dx = x -. prev_x in
              let dy = y -. prev_y in
              let dz = z -. prev_z in
              let length =
                (Float.sqrt (dx*.dx +. dy*.dy +. dz*.dz)) +. length 
              in
              let next_station = station + 1 in
              Printf.bprintf buffer "%d-%d %d-%d %f %f %f\n"
                kat_number station kat_number next_station dx dy dz;
              add_legs ~length ~station:next_station ~coords:rest
                ~prev_x:x ~prev_y:y ~prev_z:z
        in
        match
          add_legs ~length:0.0 ~station:starting_station ~coords
            ~prev_x:x ~prev_y:y ~prev_z:z
        with
        | None -> ()
        | Some (length, next_station) ->
          station := next_station;
          Out_channel.fprintf svx_writer "%s" (Buffer.contents buffer)
      end
    | _ -> ()
  end

let rec process_rows ~rows ~svx_writer =
  match rows with
  | [] -> ()
  | row::rows ->
    station := 0;
    let nummer = Csv.Row.find row "NUMMER" in
    let kat_number = Float.iround_towards_zero_exn (Float.of_string nummer) in
    let wkt = Csv.Row.find row "WKT" in
    let polygon = "POLYGON ((" in
    let multipolygon = "MULTIPOLYGON (((" in
    if String.is_prefix wkt ~prefix:polygon then begin
      let wkt = String.chop_prefix_exn wkt ~prefix:polygon in
      let wkt = String.chop_suffix_exn wkt ~suffix:"))" in
      let coords = String.split wkt ~on:',' in
      write_survex ~svx_writer ~kat_number ~coords;
      process_rows ~rows ~svx_writer
    end else if String.is_prefix wkt ~prefix:multipolygon then begin
      let wkt = String.chop_prefix_exn wkt ~prefix:multipolygon in
      let wkt = String.chop_suffix_exn wkt ~suffix:"))" in
      let rec iter wkt =
        let closing = String.index_exn wkt ')' in
        let polygon = String.sub wkt ~pos:0 ~len:closing in
        let coords = String.split polygon ~on:',' in
        write_survex ~svx_writer ~kat_number ~coords;
        if closing + 1 = String.length wkt then ()
        else
          iter (String.sub wkt ~pos:(closing + 5)
            ~len:(String.length wkt - (closing + 5)))
      in
      iter wkt;
      process_rows ~rows ~svx_writer
    end else begin
      Out_channel.eprintf "Ignoring row for kat number %d\n%!" kat_number;
      process_rows ~rows ~svx_writer
    end

let run ~shx ~svx =
  let wkt = Caml.Filename.temp_file "convert_shx" "wkt" in
  convert_to_well_known_text ~input:shx ~output:wkt;
  let wkt_csv = wkt ^ "/" ^ Caml.Filename.chop_extension shx ^ ".csv" in
  let rows = Csv.Rows.load ~separator:',' ~has_header:true wkt_csv in
  let svx_writer = Out_channel.create (svx ^ ".svx") in
  Out_channel.fprintf svx_writer "*begin %s\n" svx;
  Out_channel.fprintf svx_writer "*cs UTM33N\n";
  Out_channel.fprintf svx_writer "*cs out UTM33N\n";
  Out_channel.fprintf svx_writer "*flags surface\n";
  Out_channel.fprintf svx_writer
    "*data cartesian from to easting northing altitude\n";
  process_rows ~rows ~svx_writer;
  Out_channel.fprintf svx_writer "*end %s\n" svx;
  Out_channel.close svx_writer;
  Caml.Sys.remove wkt_csv;
  Unix.rmdir wkt

let syntax () =
  failwith "syntax: convert_shx SHX-INPUT SURVEY-NAME"

let () =
  match Caml.Sys.argv with
  | [| _; shx; svx |] -> run ~shx ~svx
  | _ -> syntax ()
